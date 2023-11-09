
## Attempt 5.0 report
I attempted to write the arcutecture that I had writen in python using generators, only of cause in C there are no generators.
Therefor I tryed to use a fucntion that is passed a struct pointer that contains intputs and outputs, as well as other data.
The intput is set by the caller, and the function uses the output as a buffer untill its ready.

If the function needs more inputs to create a propper output, it returns the boolian value true, 
and when the output is ready for for consuming somewere else, it returns false.

The output of the function is a pointer, and so when it returns false, 
the next step in the process can take over the corresponding heap memory,
while the function its self will allocate new memory and save its pointer in the output of its state.

Thus the function creates memory but does not delite it.

This allows the use of a do while loop, were the return value of the function is the while conditionn.

I want to now re-write what I have so far, because I have realised that I want the code to be stored in an "imutable" variable
and for the code that processes it to retain offsets into this memory. 
For example, I want a token to keep track of the line, collumn, offset, and length of the code that it is responsible for.

I also want to use an emum for keeping track of what kind of thing each token is.

I will probably need to use a regex engine to classify the tokens.

Also the wordiser needs to have a quote mode, which was its reson detra.
