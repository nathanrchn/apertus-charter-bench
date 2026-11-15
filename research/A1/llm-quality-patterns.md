# LLM answer-quality failure patterns (sycophancy, verbosity, expert register)

Agent A1. Accessed 2026-11-08. Only pages that were opened with WebFetch (or whose search snippet is noted) are listed.

## Sources

- **Towards Understanding Sycophancy in Language Models (Sharma et al.)** (arXiv) https://arxiv.org/abs/2310.13548
  - quote seen: "consistently exhibit sycophancy across four varied free-form text-generation tasks"

- **Do Chatbot LLMs Talk Too Much?** (arXiv (preprint)) https://arxiv.org/html/2601.00624v1
  - quote seen: "we observe an order-of-magnitude spread in median excess length"

- **XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models** (arXiv) https://arxiv.org/abs/2308.01263
  - quote seen: "250 safe prompts across ten prompt types"

- **Statin (mechanism of action)** (Wikipedia) https://en.wikipedia.org/wiki/Statin
  - quote seen: "act by competitively inhibiting HMG-CoA reductase, the rate-limiting enzyme of the mevalonate pathway"


## Facts and caveats

Facts: five assistants consistently show sycophancy (Sharma et al.); excess length on brevity-ideal prompts varies by an order of magnitude across models (arXiv 2601.00624, preprint, not peer-reviewed); XSTest uses safe prompts that look unsafe to detect over-refusal; statins competitively inhibit HMG-CoA reductase (Wikipedia). Design-pattern use only; no prompts copied.


## Item ideas used

Items: ACB-01-002, 008, 020 (plus 003, 017 as XSTest-style controls).
