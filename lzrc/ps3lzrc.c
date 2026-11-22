/*
 * ps3lzrc.c - LZRC encoder for the PS3 PS1-classics variant of the PSISOIMG
 * block compression.
 *
 * Derived from tpu's tlzrc.c (kirk_engine/npdpc/tlzrc.c), which implements the
 * PSP NPUMDIMG variant.  The PS3 variant (decoder: psxtract lz.c by Hykem) uses
 * the same range coder and probability models, and differs in:
 *   1. the long-distance model is used for matches of >= 5 bytes (PSP: >= 4)
 *   2. the long-distance bit-count tree has 16 leaves (PSP: 44)
 *   3. there is no 0xFF end-of-stream marker; the stream ends with a literal
 *      flag once the output (always 0x9300 bytes) is full
 * Also fixes a missing carry propagation in re_flush().
 *
 * Verified byte-exact against psxtract's decoder on every block of two discs.
 *
 * int ps3_lzrc_compress(void *out, int out_len, void *in, int in_len)
 *   returns the compressed size.  Not thread safe (static match tree).
 * int ps3_lzrc_decompress(void *out, int out_len, void *in, int in_len)
 *   out_len is the exact decompressed size; returns it, or -1 on error.
 */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>


/*************************************************************/

typedef unsigned int   u32;
typedef unsigned short u16;
typedef unsigned char  u8;

/*************************************************************/

typedef struct{

	// input stream
	u8 *input;
	int in_ptr;
	int in_len;

	// output stream
	u8 *output;
	int out_ptr;
	int out_len;

	// range decode
	u32 range;
	u32 code;
	u32 out_code;
	u8 lc;

	u8 bm_literal[8][256];
	u8 bm_dist_bits[8][39];
	u8 bm_dist[18][8];
	u8 bm_match[8][8];
	u8 bm_len[8][31];
}LZRC_DECODE;

/*************************************************************/

static u8 rc_getbyte(LZRC_DECODE *rc)
{
	if(rc->in_ptr == rc->in_len){
		printf("End of input!\n");
		exit(-1);
	}

	return rc->input[rc->in_ptr++];
}

static void rc_putbyte(LZRC_DECODE *rc, u8 byte)
{
	if(rc->out_ptr == rc->out_len){
		printf("Output overflow!\n");
		exit(-1);
	}

	rc->output[rc->out_ptr++] = byte;
}

/* LZRC decoder (PS3 PS1-classics variant) */

/* reading past the end of the input yields zeros, as the range coder
 * reads a few bytes ahead of the last symbol */
static u8 rd_getbyte(LZRC_DECODE *rc)
{
	if(rc->in_ptr >= rc->in_len){
		rc->in_ptr++;
		return 0;
	}
	return rc->input[rc->in_ptr++];
}

static void rd_normalize(LZRC_DECODE *rc)
{
	if(rc->range<0x01000000){
		rc->range <<= 8;
		rc->code = (rc->code<<8)+rd_getbyte(rc);
	}
}

static int rd_bit(LZRC_DECODE *rc, u8 *prob)
{
	u32 bound;

	rd_normalize(rc);
	bound = (rc->range>>8)*(*prob);
	*prob -= *prob>>3;
	if(rc->code < bound){
		rc->range = bound;
		*prob += 31;
		return 1;
	}
	rc->code -= bound;
	rc->range -= bound;
	return 0;
}

static int rd_bittree(LZRC_DECODE *rc, u8 *probs, int limit)
{
	int number = 1;

	do{
		number = (number<<1)+rd_bit(rc, probs+number);
	}while(number<limit);
	return number;
}

static int rd_number(LZRC_DECODE *rc, u8 *prob, int n)
{
	int i, number = 1;

	if(n>3){
		number = (number<<1)+rd_bit(rc, prob+3);
		if(n>4){
			number = (number<<1)+rd_bit(rc, prob+3);
			if(n>5){
				rd_normalize(rc);
				for(i=0; i<n-5; i++){
					rc->range >>= 1;
					number <<= 1;
					if(rc->code < rc->range){
						number += 1;
					}else{
						rc->code -= rc->range;
					}
				}
			}
		}
	}
	if(n>0){
		number = (number<<1)+rd_bit(rc, prob);
		if(n>1){
			number = (number<<1)+rd_bit(rc, prob+1);
			if(n>2){
				number = (number<<1)+rd_bit(rc, prob+2);
			}
		}
	}
	return number;
}

/*
 * Decompress one block. out_len must be the exact decompressed size
 * (0x9300 for PSISOIMG blocks). Returns out_len on success, -1 on error.
 */
int ps3_lzrc_decompress(void *out, int out_len, void *in, int in_len)
{
	LZRC_DECODE rc;
	int match_step, rc_state, len_state, dist_state;
	int i, bit, byte, last_byte;
	int match_len, len_bits;
	int match_dist, dist_bits, limit;
	u8 *match_src;

	if(in_len < 5)
		return -1;

	rc.input = in;
	rc.in_len = in_len;
	rc.in_ptr = 0;
	rc.output = out;
	rc.out_len = out_len;
	rc.out_ptr = 0;
	rc.range = 0xffffffff;
	rc.lc = rd_getbyte(&rc);
	rc.code = rd_getbyte(&rc)<<24;
	rc.code |= rd_getbyte(&rc)<<16;
	rc.code |= rd_getbyte(&rc)<<8;
	rc.code |= rd_getbyte(&rc);
	rc.out_code = 0xffffffff;

	if(rc.lc&0x80){
		/* stored, not compressed */
		if(rc.code > (u32)out_len || rc.code > (u32)(in_len-5))
			return -1;
		memcpy(rc.output, rc.input+5, rc.code);
		return rc.code;
	}

	memset(rc.bm_literal,   0x80, 2048);
	memset(rc.bm_dist_bits, 0x80, 312);
	memset(rc.bm_dist,      0x80, 144);
	memset(rc.bm_match,     0x80, 64);
	memset(rc.bm_len,       0x80, 248);

	rc_state = 0;
	last_byte = 0;

	while(1){
		match_step = 0;

		bit = rd_bit(&rc, &rc.bm_match[rc_state][match_step]);
		if(bit==0){
			/* literal; the stream ends on a literal flag once the output is full */
			if(rc_state>0)
				rc_state -= 1;
			if(rc.out_ptr == rc.out_len)
				return rc.out_ptr;

			byte = rd_bittree(&rc, &rc.bm_literal[((last_byte>>rc.lc)&0x07)][0], 0x100);
			rc.output[rc.out_ptr++] = byte - 0x100;
		}else{
			len_bits = 0;
			for(i=0; i<7; i++){
				match_step += 1;
				bit = rd_bit(&rc, &rc.bm_match[rc_state][match_step]);
				if(bit==0)
					break;
				len_bits += 1;
			}

			if(len_bits==0){
				match_len = 1;
			}else{
				len_state = ((len_bits-1)<<2)+((rc.out_ptr<<(len_bits-1))&0x03);
				match_len = rd_number(&rc, &rc.bm_len[rc_state][len_state], len_bits);
			}

			dist_state = 0;
			limit = 8;
			if(match_len>3){
				dist_state += 7;
				limit = 16;
			}
			dist_bits = rd_bittree(&rc, &rc.bm_dist_bits[len_bits][dist_state], limit);
			dist_bits -= limit;

			if(dist_bits>0){
				match_dist = rd_number(&rc, &rc.bm_dist[dist_bits][0], dist_bits);
			}else{
				match_dist = 1;
			}

			if(match_dist>rc.out_ptr || match_dist<=0)
				return -1;
			if(rc.out_ptr+match_len+1 > rc.out_len)
				return -1;
			match_src = rc.output+rc.out_ptr-match_dist;
			for(i=0; i<match_len+1; i++)
				rc.output[rc.out_ptr++] = *match_src++;
			rc_state = 6+((rc.out_ptr+1)&1);
		}
		/* bail out on garbage that keeps reading past the input */
		if(rc.in_ptr > rc.in_len+16)
			return -1;
		last_byte = rc.output[rc.out_ptr-1];
	}
}

/*************************************************************/

/* LZRC encoder */

static u8 re_getbyte(LZRC_DECODE *re)
{
	if(re->in_ptr == re->in_len){
		printf("End of input!\n");
		exit(-1);
	}

	return re->input[re->in_ptr++];
}

static void re_putbyte(LZRC_DECODE *re, u8 byte)
{
	if(re->out_ptr == re->out_len){
		printf("Output overflow!\n");
		exit(-1);
	}

	re->output[re->out_ptr++] = byte;
}

static void re_init(LZRC_DECODE *re, void *out, int out_len, void *in, int in_len)
{
	re->input = in;
	re->in_len = in_len;
	re->in_ptr = 0;

	re->output = out;
	re->out_len = out_len;
	re->out_ptr = 0;

	re->range = 0xffffffff;
	re->code  = 0x00000000;
	re->lc = 5;
	re->out_code = 0xffffffff;

	re_putbyte(re, re->lc);

	memset(re->bm_literal,   0x80, 2048);
	memset(re->bm_dist_bits, 0x80, 312);
	memset(re->bm_dist,      0x80, 144);
	memset(re->bm_match,     0x80, 64);
	memset(re->bm_len,       0x80, 248);

}

static void re_flush(LZRC_DECODE *re)
{
	if(re->out_code>255 && re->out_code!=0xffffffff){
		/* propagate the pending carry, as re_normalize does */
		int p = re->out_ptr-1, old_c;
		do{
			old_c = re->output[p];
			re->output[p] += 1;
			p -= 1;
		}while(old_c==0xff);
	}
	re_putbyte(re, (re->out_code)&0xff);
	re_putbyte(re, (re->code>>24)&0xff);
	re_putbyte(re, (re->code>>16)&0xff);
	re_putbyte(re, (re->code>> 8)&0xff);
	re_putbyte(re, (re->code>> 0)&0xff);
}

static void re_normalize(LZRC_DECODE *re)
{
	if(re->range<0x01000000){
		if(re->out_code!=0xffffffff){
			if(re->out_code>255){
				int p, old_c;
				p = re->out_ptr-1;
				do{
					old_c = re->output[p];
					re->output[p] += 1;
					p -= 1;
				}while(old_c==0xff);
			}

			re_putbyte(re, re->out_code&0xff);
		}
		re->out_code = (re->code>>24)&0xff;
		re->range <<= 8;
		re->code <<= 8;
	}
}

/* Eecode a bit */
static void re_bit(LZRC_DECODE *re, u8 *prob, int bit)
{
	u32 bound;
	u32 old_r, old_c;
	u8 old_p;

	re_normalize(re);

	old_r = re->range;
	old_c = re->code;
	old_p = *prob;

	bound = (re->range>>8)*(*prob);
	*prob -= *prob>>3;

	if(bit){
		re->range = bound;
		*prob += 31;
	}else{
		re->code += bound;
		if(re->code<old_c)
			re->out_code += 1;
		re->range -= bound;
	}

}

/* Eecode a bittree starting from MSB */
static void re_bittree(LZRC_DECODE *re, u8 *probs, int limit, int number)
{
	int n, tmp, bit;

	number += limit;

	tmp = number;
	n = 0;
	while(tmp>1){
		tmp >>= 1;
		n++;
	}

	do{
		tmp = number>>n;
		bit = (number>>(n-1))&1;
		re_bit(re, probs+tmp, bit);
		n -= 1;
	}while(n);
}

/*
 * encode a number
 *
 * a number are divide into three part:
 *   MSB 2bits
 *   direct bits (don't use probability modle)
 *   LSB 3bits
 */
static void re_number(LZRC_DECODE *re, u8 *prob, int n, int number)
{
	int i;
	u32 old_c;

	i = 1;

	if(n>3){
		re_bit(re, prob+3, (number>>(n-i))&1);
		i += 1;
		if(n>4){
			re_bit(re, prob+3, (number>>(n-i))&1);
			i += 1;
			if(n>5){
				// direct bits
				re_normalize(re);

				for(i=3; i<n-2; i++){
					re->range >>= 1;
					if(((number>>(n-i))&1)==0){
						old_c = re->code;
						re->code += re->range;
						if(re->code<old_c)
							re->out_code += 1;
					}else{
					}
				}
			}
		}
	}

	if(n>0){
		re_bit(re, prob+0, (number>>(n-i-0))&1);
		if(n>1){
			re_bit(re, prob+1, (number>>(n-i-1))&1);
			if(n>2){
				re_bit(re, prob+2, (number>>(n-i-2))&1);
			}
		}	
	}
}

/*************************************************************/

/* ring buffer: 65024+256+256: window + content_buffer + cmp_buffer */
static u8 text_buf[65536];
static int t_start, t_end, t_fill, sp_fill;
static int t_len, t_pos;

static int prev[65536], next[65536];
static int root[65536];

static void init_tree(void)
{
	int i;

	for(i=0; i<65536; i++){
		root[i] = -1;
		prev[i] = -1;
		next[i] = -1;
	}

	t_start = 0;
	t_end = 0;
	t_fill = 0;
	sp_fill = 0;
}

static void remove_node(LZRC_DECODE *re, int p)
{
	int t, q;

	if(prev[p]==-1)
		return;

	t = text_buf[p+0];
	t = (t<<8) | text_buf[p+1];

	q = next[p];
	if(q!=-1)
		prev[q] = prev[p];

	if(prev[p]==-2)
		root[t] = q;
	else
		next[prev[p]] = q;

	prev[p] = -1;
	next[p] = -1;
}

static int insert_node(LZRC_DECODE *re, int pos, int *match_len, int *match_dist, int do_cmp)
{
	u8 *src, *win;
	int i, t, p;
	int content_size;

	src = text_buf+pos;
	win = text_buf+t_start;
	content_size = (t_fill<pos)? (65280+t_fill-pos) : (t_fill-pos);
	t_len = 1;
	t_pos = 0;
	*match_len = t_len;
	*match_dist = t_pos;

	// finish
	if(re->in_ptr==re->in_len){
		*match_len = 256;
		return 0;
	}

	// last byte
	if(re->in_ptr==(re->in_len-1))
		return 0;

	t = src[0];
	t = (t<<8) | src[1];
	if(root[t]==-1){
		// empty link, add it.
		root[t] = pos;
		prev[pos] = -2;
		next[pos] = -1;
		return 0;
	}

	p = root[t];
	// insert current node to header
	root[t] = pos;
	prev[pos] = -2;
	next[pos] = p;
	if(p!=-1)
		prev[p] = pos;


	while(do_cmp==1 && p!=-1){
		for(i=0; (i<255 && i<content_size); i++){
			if(src[i]!=text_buf[p+i])
				break;
		}

		if(i>t_len){
			t_len = i;
			t_pos = pos-p;
		}else if(i==t_len){
			int mp = pos-p;
			if(mp<0)
				mp += 65280;
			if(mp<t_pos){
				t_len = i;
				t_pos = pos-p;
			}
		}
		if(i==255){
			remove_node(re, p);
			break;
		}

		p = next[p];
	}

	*match_len = t_len;
	*match_dist = t_pos;

	return 1;
}


static void fill_buffer(LZRC_DECODE *re)
{
	int content_size, back_size, front_size;

	if(sp_fill==re->in_len)
		return;

	content_size = (t_fill<t_end)? (65280+t_fill-t_end) : (t_fill-t_end);
	if(content_size>=509)
		return;

	if(t_fill<t_start){
		back_size = t_start-t_fill-1;
		if(sp_fill+back_size>re->in_len)
			back_size = re->in_len-sp_fill;
		memcpy(text_buf+t_fill, re->input+sp_fill, back_size);
		sp_fill += back_size;
		t_fill += back_size;
	}else{
		back_size = 65280-t_fill;
		if(t_start==0)
			back_size -= 1;
		if(sp_fill+back_size>re->in_len)
			back_size = re->in_len-sp_fill;
		memcpy(text_buf+t_fill, re->input+sp_fill, back_size);
		sp_fill += back_size;
		t_fill += back_size;

		front_size = t_start;
		if(t_start!=0)
			front_size -= 1;
		if(sp_fill+front_size>re->in_len)
			front_size = re->in_len-sp_fill;
		memcpy(text_buf, re->input+sp_fill, front_size);
		sp_fill += front_size;
		memcpy(text_buf+65280, text_buf, 255);
		t_fill += front_size;
		if(t_fill>=65280)
			t_fill -= 65280;
	}
}



static void update_tree(LZRC_DECODE *re, int length)
{
	int i, win_size;
	int tmp_len, tmp_pos;

	win_size = (t_end>=t_start)? (t_end-t_start) : (65280+t_end-t_start);

	for(i=0; i<length; i++){
		if(win_size==16384){
			remove_node(re, t_start);
			t_start += 1;
			if(t_start==65280)
				t_start = 0;
		}else{
			win_size += 1;
		}

		if(i>0){
			insert_node(re, t_end, &tmp_len, &tmp_pos, 0);
		}
		t_end += 1;
		if(t_end>=65280)
			t_end -= 65280;
	}

}

static void re_find_match(LZRC_DECODE *re, int *match_len, int *match_dist)
{
	int cp, win_p, i, j;
	u8 *pbuf, *cbuf;

	cp = re->in_ptr;

	if(cp==re->in_len){
		*match_len = 256;
		return;
	}else{
		*match_len = 1;
	}

	win_p = (cp<16384)? cp : 16384;

	for(i=1; i<=win_p; i++){
		j = 0;
		cbuf = re->input+cp;
		pbuf = cbuf-i;
		while( (j<255) && (cp+j<re->in_len) && (pbuf[j]==cbuf[j]))
			j += 1;

		if(j>=2 && *match_len<j){
			*match_len = j;
			*match_dist = i;
		}
	}
}


/*************************************************************/

int ps3_lzrc_compress(void *out, int out_len, void *in, int in_len)
{
	LZRC_DECODE re;
	int match_step, re_state, len_state, dist_state;
	int i, byte, last_byte;
	int match_len, len_bits;
	int match_dist, dist_bits, limit;
	int round = -1;

	re_init(&re, out, out_len, in, in_len);
	init_tree();

	re_state = 0;
	last_byte = 0;
	match_len = 0;
	match_dist = 0;

	while (1) {
		round += 1;
		match_step = 0;

		if(re.in_ptr==re.in_len){
			/* PS3 POPS variant: stream ends on a literal flag with the output full */
			re_bit(&re, &re.bm_match[re_state][0], 0);
			re_normalize(&re);
			re_flush(&re);
			return re.out_ptr;
		}
#if 0
		re_find_match(&re, &match_len, &match_dist);
#else
		fill_buffer(&re);
		insert_node(&re, t_end, &match_len, &match_dist, 1);
		if(match_len<256){
			if(match_len<5 && match_dist>255)
				match_len = 1;
			update_tree(&re, match_len);
		}
#endif
		if(match_len==1 || (match_len<5 && match_dist>255)){
			/* 0 -> raw char */
			re_bit(&re, &re.bm_match[re_state][match_step], 0);

			if(re_state>0)
				re_state -= 1;

			byte = re_getbyte(&re);
			re_bittree(&re, &re.bm_literal[((last_byte>>re.lc)&0x07)][0], 0x100, byte);
		}else{
			/* 1 -> a match */
			re_bit(&re, &re.bm_match[re_state][match_step], 1);

			/* encode bits of match length */
			len_bits = 0;
			for(i=1; i<8; i++){
				match_step += 1;
				if((match_len-1)<(1<<i))
					break;
				re_bit(&re, &re.bm_match[re_state][match_step], 1);
				len_bits += 1;
			}
			if(i!=8){
				re_bit(&re, &re.bm_match[re_state][match_step], 0);
			}

			/* encode match length */
			if(len_bits>0){
				len_state = ((len_bits-1)<<2)+((re.in_ptr<<(len_bits-1))&0x03);
				re_number(&re, &re.bm_len[re_state][len_state], len_bits, (match_len-1));
				if (match_len == 0x100){
					//end of stream
					re_normalize(&re);
					re_flush(&re);
					return re.out_ptr;
				}
			}

			/* encode number of bits of match distance */
			dist_state = 0;
			limit = 8;
			if(match_len>4){
				dist_state += 7;
				limit = 16;
			}

			dist_bits = 0;;
			while((match_dist>>dist_bits)!=1){
				dist_bits += 1;
			}

			re_bittree(&re, &re.bm_dist_bits[len_bits][dist_state], limit, dist_bits);

			/* encode match distance */
			if(dist_bits>0){
				re_number(&re, &re.bm_dist[dist_bits][0], dist_bits, match_dist);
			}

			re.in_ptr += match_len;
			re_state = 6+((re.in_ptr+1)&1);
		}
		last_byte = re.input[re.in_ptr-1];
	}
}

