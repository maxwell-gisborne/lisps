#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>

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

// storage i should be the (i-1)th charicter,
// if there are N charicters on a line that starts at S, then S+N should index \n or EOF
// line breaks should be an array of offsets j, such that j indexes an \n or an EOF
typedef struct {
    size_t lines;
    size_t* line_breaks;
    char* storage;
} Document;

void Document_Free(Document* doc) {
    free(doc->storage);
    free(doc->line_breaks);
    free(doc);
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


    doc->storage = realloc(doc->storage,
            end_of_new_line*sizeof(char));

    if (doc->storage == NULL) perror("failed to alloc storage");

    for (int i=0; i<string->len; i++){
        doc->storage[ start_of_new_line + i ] = string->cont[i];
    }

    doc->line_breaks[doc->lines] = end_of_new_line;
    if (end_of_old_line != 0) doc->storage[end_of_old_line] = '\n';
    doc->storage[end_of_new_line] = '\0';
    doc->lines ++;
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

int main (int argc, char** argv){ 

    Document code;
    code.lines = 0;
    code.line_breaks = malloc(0);
    code.storage = malloc(0);

    while (true) {
        Str input = readline(str("> "));
        if (Str_Equal(str("stop"), input)) break;
        Document_append(&code, &input);
    }
}
