# Deep Research

Searchers:

1. Display to the user the tokens used (including per-file like in AI Studio) and available tokens for input and output.
    
2. Ability to set ratios for what portion of research relative to available output tokens to fill from provided files, from provided links, and from search.
    
3. Remove the limitation on uploaded chat files, replacing it with information about remaining tokens.
    
4. When there's insufficient context window for output at the requested depth, offer the user a new chat with the previous chat and its results passed into some kind of RAG for the subsequent chat.
    
5. Ability to select other Gemini chats and their results as data sources.
    
6. When using research from another chat as a source, reuse citations when quoting its parts if in the original file the quoted part is a citation with a source reference.
    
7. When large-scale research is needed that can only be realized at the required scope (for example, when the user explicitly specifies expected character count or A4 pages) by breaking it into parts, form a plan, divide it among agents, queue them, and pass RAG context from previous ones to each subsequent agent.
    
8. Allow users to intervene in the research process by pausing it (like in Manus). After receiving new instructions, adjust the remaining unexecuted plan and continue.
    
9. In situations where searching and analyzing sources doesn't provide answers to questions posed in the prompt, don't finish the research having only covered part of it—pause it and ask the user: "Can't find answers to these questions. What should I do: a. prepare analysis based on what I found, or b. will you provide links and sources to cover the question?"
    
10. Give users a choice of how to export formulas: TeX/LaTeX or ready mathematical notation like in Word formulas.
    
11. Add converters to MD format for common files like PDF, DOCX. Offer users to preemptively convert them to MD format before using them in context.
    
12. Teach it to follow instructions better. Perhaps, for example, train it on keywords that control the process. If, for instance, a user explicitly describes <Search Process>, <Reasoning>, <Writing Style>, <Links for Search>, <Output Format>, etc., then strictly follow them. This would imply that a user who composed such a prompt clearly understands what they want to get, and in this chat there's no need to simplify.
    

P.s. 13) Enable the ability to use Gems with Deep Research mode to pass both context and writing style to the research.

Upvote53Downvote