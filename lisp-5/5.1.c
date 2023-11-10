#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>
#include <regex.h>

typedef struct {
    size_t len;
    char* cont;
} Str;

Str string(size_t len, char* cont){
    Str string = {.len=len, .cont=cont};
    return string;
}


Str str(char* cont){
    int i=0;
    while (true){
        if (cont[i] == '\0') return string(i, cont);
        i++;
    }
}

void Str_append(Str *string,char c){
    string->len ++;
    string->cont = realloc(string->cont, string->len*sizeof(char)+1);
    string->cont[string->len] = '\0';
    string->cont[string->len-1] = c;
}

void printstr(Str string){
    for (size_t i=0; i< string.len; i++){
        putchar(string.cont[i]);
    }
}

void Str_Free (Str* string) {
    free(string->cont);
    free(string);
};

bool Str_Equal(Str a, Str b){
    if (a.len != b.len) return false;
    for (int i=0; i<a.len; i++){
        if (a.cont[i] != b.cont[i]) return false;
    }
    return true;
}

typedef struct {
    size_t len;
    void** callbacks;
} Callbacks;

// raw i should be the (i-1)th charicter,
// if there are N charicters on a line that starts at S, then S+N should index \n or EOF
// line breaks should be an array of offsets j, such that j indexes an \n or an EOF
typedef struct {
    size_t lines;
    size_t* line_breaks;
    char* raw;
    size_t word_count;
    Str* words;
    Callbacks append_callbacks;
} Document;

void Document_Free(Document* doc) {
    free(doc->raw);
    free(doc->line_breaks);
    free(doc);
}


void push_word(Document *doc, Str *buffer){
    // add word to word count
    doc->word_count ++;
    doc->words = realloc(doc->words, doc->word_count*sizeof(Str));
    assert(doc->words != NULL);
    doc->words[doc->word_count-1] = *buffer;

    // reset buffer
    buffer->len = 0;
    buffer->cont = malloc(1);
    buffer->cont[0] = '\0';
}


void Document_append(Document* doc, Str* string){
    doc->line_breaks = realloc( doc->line_breaks,
            (doc->lines+1)*sizeof(size_t));
    if (doc->line_breaks == NULL) perror("failed to alloc linebreakes");

    size_t end_of_old_line;
    size_t start_of_new_line;
    size_t end_of_new_line;

    if (doc->lines == 0) {
        end_of_old_line = 0;
        start_of_new_line = 0;
        end_of_new_line = string->len;
    } else {
        end_of_old_line = doc->line_breaks[doc->lines-1];
        start_of_new_line = end_of_old_line +1;
        end_of_new_line = start_of_new_line + string->len;
    }


    doc->raw = realloc(doc->raw,
            end_of_new_line*sizeof(char));

    if (doc->raw == NULL) perror("failed to alloc raw");

    for (int i=0; i<string->len; i++){
        doc->raw[ start_of_new_line + i ] = string->cont[i];
    }

    typedef enum {NORMAL_MODE, QUOTE_MODE} MODE;
    MODE mode = NORMAL_MODE;
    char quote_char;
    Str buffer;
    if (doc->raw[end_of_old_line] == '"'
       |doc->raw[end_of_old_line] == '\''){
        mode = QUOTE_MODE;
        quote_char = doc->raw[end_of_old_line];
        doc->word_count --;
        buffer = doc->words[doc->word_count];
    } else{
        buffer.len = 0;
        buffer.cont = malloc(1);
        buffer.cont[0] = '\0';
    }

    doc->line_breaks[doc->lines] = end_of_new_line;
    if (end_of_old_line != 0) doc->raw[end_of_old_line] = '\n';
    doc->lines ++;

    for (int i=start_of_new_line; i<end_of_new_line; i++){
        switch(mode){
            case NORMAL_MODE:
                if ( doc->raw[i] == ' '
                   | doc->raw[i] == '\t') {
                    push_word(doc, &buffer);
                    break;
                }
                if (doc->raw[i] == '"'
                   |doc->raw[i] == '\''){
                    if (buffer.len != 0) push_word(doc, &buffer);
                    quote_char = doc->raw[i];
                    mode = QUOTE_MODE;
                    break;
                }
                Str_append(&buffer,doc->raw[i]);
                break;

            case QUOTE_MODE:
                if (doc->raw[i] == quote_char){
                    push_word(doc, &buffer);
                    mode=NORMAL_MODE;
                    break;
                };
                Str_append(&buffer,doc->raw[i]);
                break;
        }
    }
    
    switch(mode){
        case NORMAL_MODE:
            if (buffer.len != 0){
                push_word(doc, &buffer);
                doc->raw[end_of_new_line] = '\0';
            } else {
                free(buffer.cont);
            }
            break;
        case QUOTE_MODE:
            Str_append(&buffer, '\n');
            push_word(doc, &buffer);
            doc->raw[end_of_new_line] = quote_char;
            break;
    }



    for (size_t ci=0; ci < doc->append_callbacks.len; ci++){
        void (*callback)(Document*, size_t) = doc->append_callbacks.callbacks[ci];
        callback(doc, doc->lines-1);
    }
}

typedef struct {
    bool okay;
    Str result;
} Document_get_line_Result;

Document_get_line_Result Document_get_line(Document* doc, size_t n){
    if (n > doc->lines) {
        Document_get_line_Result return_value = {.okay = false};
        return return_value;
    }
    size_t start = n==0 ? 0 : doc->line_breaks[n-1]+1;
    size_t end = doc->line_breaks[n];
    assert( end > start);

    size_t len = end-start;
    char* cont = malloc(len*sizeof(char));
    for (int i=0; i< len; i++) cont[i] = doc->raw[start+i];
    cont[end] = '\0';

    Document_get_line_Result return_value = {
        .okay = true,
        .result = {
            .len=end-start,
            .cont = cont,
        }
    };
    return return_value;
}

Str readline(Str prompt){
    assert(prompt.cont[prompt.len] == '\0');
    printf("%s", prompt.cont);
    char* input;
    size_t buffer_length = 0;
    size_t len = getline(&input, &buffer_length, stdin );
    assert(len != -1);
    return string(len-1, input);
}

void Document_print(Document* doc){
    for (int i=0; i<doc->lines; i++){
        Document_get_line_Result result = Document_get_line( doc, i);
        if (!result.okay) printf("Error\n");
        Str line = result.result;
        printf("%3i| %s\n", i, line.cont);
    }
}


void Tokenize_line(Document *doc, size_t line_number){
    printf("I should do some rejex or something\n");
    int reti;
}

int main (int argc, char** argv){ 

    regex_t regex;
    assert(regcomp(&regex,"",0) == 0);

    Document code;
    code.lines = 0;
    code.line_breaks = malloc(0);
    code.raw = malloc(0);
    code.append_callbacks.len = 0;
    code.append_callbacks.callbacks = malloc(sizeof(void*));
    code.append_callbacks.callbacks[0] = Tokenize_line;
    code.word_count = 0;
    code.words = malloc(0);

    while (true) {
        Str input = readline(str("> "));
        if (Str_Equal(str("stop"), input)) break;
        Document_append(&code, &input);
    }
    Document_print(&code);
}
