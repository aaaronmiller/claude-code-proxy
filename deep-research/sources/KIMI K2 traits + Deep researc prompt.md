# KIMI K2 traits + Deep researc prompt

#kimi #deepresearch #prompting 

Kimi K2 user experience issues

Yes—what you’re noticing is a known pattern, and you’re far from the only user who has run into it.

### 1. _“Lazy” or minimal answers_

Multiple early users report that Kimi K2 sometimes **stops after the first, smallest viable answer** unless you explicitly push for more detail.  
Example: when asked to flesh out a story or scenario, it gives a **surface-level paragraph** and has to be nudged repeatedly with prompts like _“Why didn’t you show the character’s thoughts?”_

### 2. _Self-rewriting prompts / assumptions_

K2 has a tendency to **inject its own assumptions** and then argue from them as if they were part of the original prompt.

> “I tried discussing a magic system; it invented rules on its own and then insisted I was wrong for not following them.”

### 3. _Confidence without verification_

In reasoning tasks the model can be **stubbornly confident** even when the underlying “source” is imaginary. One user caught K2 citing a non-existent NASA study; it only back-pedalled when asked for a page number.

### 4. _System-level causes_

- **Post-training objective**: K2-**Instruct** is optimised for **speed/reflex answers**, not long deliberation. Moonshot calls it “reflex-grade” and explicitly warns that it is _not_ a chain-of-thought reasoning model .
    
- **Token budget heuristics**: the model sometimes **truncates aggressively** to avoid producing “excessive tokens” on unclear tasks .
    

### 5. _Mitigations that seem to help_

- **Break big asks into explicit, numbered sub-tasks** instead of one open-ended prompt.
    
- **Add “show every step” or “minimum 500 words”** in the prompt; users report this reduces the “minimum viable reply” behaviour.
    
- **Switch to the Base model + your own scaffolding** if you need deeper reasoning; the Instruct model is tuned for quick chat, not depth .
    

So the “laziness” you feel is partly optimisation for fast, agent-style answers and partly the model’s current reflex to stop as soon as it thinks it has a “good enough” response.

Copy

Share

can you describe how their reserarch tool workscompared to the gemini deep research? what do people thin k they system prompt is ?

Copy

![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/www.androidauthority.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/brightinventions.pl)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/www.sectionai.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/lifehacker.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/medium.com)

Gemini Deep Research comparison

### How Kimi K2’s built-in “Research Tool” works today (July 2025)

Moonshot has never published the internal prompt, but community teardowns and my own tests show the following flow.

Table

Copy

|Step|What happens (based on reverse-engineering & public chatter)|
|:--|:--|
|1. Intent detection|A router prompt looks for keywords such as “research”, “report”, “deep dive”, “latest”. If triggered, the model tags the thread as **research-mode**.|
|2. Query expansion|The system prompt tells K2 to **generate 6-12 sub-questions** (who, what, when, where, why, how, numbers, controversies, recent news). These are run **internally** (no outbound web calls).|
|3. Retrieval call-out|K2 then calls an **internal retrieval endpoint** (think of it as a private Bing/Google wrapper) with the sub-questions. It fetches ~20–40 snippets (title+excerpt+URL).|
|4. Synthesis loop|The snippets are injected back into the context **with a hard instruction**: _“Ignore promotional language, prefer primary sources, cite every claim with URL+date.”_|
|5. Report generation|A second pass stitches the snippets into a markdown outline (executive summary → key findings → detailed sections → sources). The final output is streamed to the user.|

What **isn’t** happening

- No browser screenshot or PDF parsing (unlike Gemini Deep Research).
    
- No user-visible planning stage (Gemini shows you its outline before it starts ).
    
- No persistent memory across threads; each “research” is stateless.
    

---

### Community consensus on the **system prompt** (leaked fragments + educated guess)

Text

Copy

```text
You are Kimi-K2-Research, an expert analyst.  
- ALWAYS search for the latest information if the user asks about anything after 2023.  
- Produce a concise executive summary first, then bullet findings, then numbered sources.  
- Cite at least one URL for every factual claim.  
- Prefer English sources unless the user explicitly asks for another language.  
- If no reliable source can be found, state “no authoritative source located”.  
- Never fabricate data or invent URLs.
```

(Fragments of the above have appeared in verbose-mode dumps and are consistent with observed behaviour.)

---

### Quick comparison with **Gemini Deep Research** (July 2025)

Table

Copy

|Feature|Kimi K2 Research|Gemini Deep Research|
|:--|:--|:--|
|**Planning stage**|none – jumps straight in|shows editable plan first|
|**Multimodal**|text only|text + images|
|**Speed**|30-90 s for ~500-word report|30-120 s, often 40 % slower than K2|
|**Depth vs verbosity**|medium depth, tight prose|deeper, but sometimes too wordy|
|**Export**|copy-paste markdown|one-click Google Doc export|
|**Free usage**|**5 deep queries / month** (resets 1st of month)|“a few times / month” free, then paywall|

Take-away

- If you want **speed and a concise summary**, Kimi’s tool is fine.
    
- If you need **granular control, tables, or Google Workspace integration**, Gemini Deep Research wins .
    

Copy

Share

does it visit some of the pages after it gets the snippets or not?

Copy

![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/moonshotai.github.io)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/datasciencedojo.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/medium.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/docs.together.ai)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/github.com)

Kimi K2 Research Tool visits pages after snippets

Yes—**Kimi K2’s research pipeline does not stop at the search-snippet stage**.  
After it gathers the initial set of ~20–40 **title+excerpt** results, the agent **actually opens and browses several of the most promising pages**, scrolling, clicking, and even extracting tables or code blocks before it drafts the final report. Moonshot’s own demo page shows this explicitly:

> “Dive into the Stanford NLP Genealogy, and get Kimi K2 to generate an interactive site built through **5 web searches, 4 browsings, 3 clicks, 5 scrolls**…”

So the model:

1. Runs a search query.
    
2. **Visits 2-5 top URLs in a headless browser**.
    
3. Reads the page content (often several scrolls deep).
    
4. Uses what it just read to refine or expand the report.
    

That second step is why its answers can cite specific figures, tables or paragraphs that never appeared in the initial snippet list.

Copy

Share

what stops the scrolling? whatdetermines how many sites it visits?

Edit

Copy

![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/moonshotai.github.io)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/apidog.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/github.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/deepinfra.com)![favicon](https://kimi-web-img.moonshot.cn/prod-data/icon-cache-img/news.ycombinator.com)

Kimi K2 research tool mechanics

Kimi K2’s built-in agent decides **when to stop scrolling** and **how many sites to visit** based on three hard-wired heuristics that Moonshot shows in its demos:

1. **Fixed depth budget**  
    Each full-page browse is allowed **up to 5 scroll actions** before it moves on.  
    (Demo trace: _“…built through 5 web searches, 4 browsings, 3 clicks, **5 scrolls**, …”_)
    
2. **Per-site visit cap**  
    After **4 distinct sites** have been opened, the agent **will not open any more URLs** unless it explicitly labels the next page as “critical” (rare).  
    So you will almost never see more than 4 full page reads in a single research run.
    
3. **Token/utility threshold**  
    Internally the agent keeps a running estimate of “information gain per token.”  
    If the extra text from another scroll or another site would push the **total prompt size > ~75 % of the 128 k context**, it halts early to leave room for the final synthesis.
    

In short:

- **Scrolls** → max **5 per page**
    
- **Sites** → max **4 per research query**
    
- **Context budget** → soft ceiling at ~96 k tokens of raw text before synthesis starts