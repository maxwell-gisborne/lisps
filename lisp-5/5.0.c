#include <stdbool.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>
#include <threads.h>

typedef struct {
    size_t len;
    char* cont;
} str;

typedef struct {
    int i;
    size_t N;
    str* output; // pointer to a string
    char input; // pointer to a single charicter
} WordifyState;

bool wordify(WordifyState* state){
    if (state->i == 0) {
        state->N = 10;
        str* new_output;
        new_output = malloc(sizeof(str));
        new_output->cont = malloc(state->N * sizeof(char));
        state->output = new_output;
    }

    if (      (state->input == (char)'\n')
            | (state->input == (char)' ')
            | (state->input == (char)'\t')) {
        state->output->cont[state->i+1] = '\0'; // make sure it ends in null terminator
        state->output->len = state->i; // set the length field
        state->output->cont = realloc( // shrink the memory untill its fits snug.
                state->output->cont,
                state->output->len*sizeof(char));
        return false;
    }


    state->output->cont[state->i] = state->input;
    state->i ++;

    if (state->i+1 == state->N) {
        state->N += 10;
        state->output->cont = realloc(state->output->cont, state->N*sizeof(char));
    }

    return true;
}


typedef struct{
    char* type;
    str* raw;
    str* content;
} Token;

typedef struct {
    str* input;
    Token* output;
} TokenizerState;

bool Tokenizer(TokenizerState* state){
    state->output = malloc(sizeof(Token));
    state->output->raw = state->input;
    state->output->type = "word";
    state->output->content = state->input;
    return !strcmp("end", state->output->content->cont);
}

int main (int argc, char** argv){ 

    WordifyState wordifystate = {
        .i = 0,
        .output = NULL,
        .input = '\0',
    };

    TokenizerState tokenizerstate;

    char* user_input;
    size_t buffer_length = 0;
    ssize_t input_length;

    do {
        printf("> ");
        input_length = getline(&user_input, &buffer_length, stdin );
        if ( input_length == -1 ) perror("OH No!");

        int j;
        do  {
            wordifystate.input = user_input[j];
            j++;
            if (j == input_length) wordifystate.input = '\n';

        } while (wordify(&wordifystate));

        tokenizerstate.input = wordifystate.output;
    } while (Tokenizer(&tokenizerstate));
    printf("done\n");
}
