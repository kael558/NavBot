# NavBot

## Input types
 - Voice - Speech recognition
 - Eyes - Eye tracker
 - Hands - Keyboard + Mouse (default)

## Output types
 - Audio
 - Visual (default)

## NavBot Keyword Commands:
 - Change Language - Change language
 - Help - Help menu
 - Exit Program - Exit program
 - Input - Change input type
 - Output - Change output type

## Main
 - What do you want to do? 
 - User states their main objective: LLM may
   - issue instructions to NavBot -> describe web contents and options for user
   - ask the user to clarify

 - thread is waiting to receive input (from any source)
   - if input is audio, then transcribe to english and send instructions to crawler 
   - if input is video, 
 - perform action and output results
   - if action could not be performed. Append to response.
 - output
   - if output is audio, then describe the contents of the website and output possible actions.
 - "NavBot Settings" is a keyword to access the settings
   - Change language
   - Help - lists all settings and what it can do
   - Change input type
   - Change output type
   - Disable/Enable keyword speaking. 

## Settings Implementation
 - Transcription recognize keyword (Hey NavBot)
 - VectorDB for identifying instruction to setting
 - Use LLM for parsing results of instruction
 - Use VectorDB to verify results of instruction

## TODO
 - [ ] Settings implementation
 - [ ] Implement mic input and transcription module - https://platform.openai.com/docs/guides/speech-to-text/prompting
 - [ ] Implement eye tracker input module
 - [ ] Implement keyboard input module
 - [ ] Implement audio output module
 - [ ] Implement simpler visual output module
 - [ ] Connect inputs to crawler
 - [ ] Handle reading output for different module

## Extra
 - [ ] Colorblindness handling
 - [ ] Large text
 - [ ] High contrast
 - [ ] Remove pop ups
 - [ ] Salient information only
 - [ ] Answer questions about images

## Code Flow
1. Ask user for input
2. Navigate to web page
3. Read web page, summarize contents, get links, key elements
4. Should I continue to issue commands and navigate or should I ask the user to clarify?
5. If i ask the user to clarify, I will describe the web page to them and what options they have.



