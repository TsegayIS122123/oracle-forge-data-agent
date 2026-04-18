# Signal Corps Articles — Team Mistral (TRP1)

## Overview

This document contains all published long-form technical articles and posts created by the Signal Corps during the Oracle Forge challenge.

The focus of these articles is not project promotion, but documenting real engineering work, failures, and system-level insights.

---

## Post 1 — Claude Code Architecture Insights

### LinkedIn
https://www.linkedin.com/posts/team-mistral_what-anthropics-accidental-code-leak-teaches-activity-7448602424749137922-3S3H

### Medium
https://medium.com/@team-mistral/the-npm-leak-nobody-read-as-an-engineering-paper-58bdd8cdea1a

### X Thread
https://x.com/TsegayAsse64592/status/2042899334992195968

### Focus
- Claude Code memory architecture
- Tool separation and permission boundaries
- System design patterns for reliable AI agents

---

## Post 2 — Building a Production Data Agent

### LinkedIn
https://www.linkedin.com/feed/update/urn:li:activity:7448646409370787840

### Medium
https://medium.com/@tsegayassefa27/what-we-learned-fixing-our-ai-agent-80-100-fac4c1b0e87f

### X Thread
https://x.com/TsegayAsse64592/status/2043727894116004035

### Focus
- DataAgentBench system design
- Knowledge Base (KB v1) architecture
- Early failures and system misalignment

---

## Post 3 — Context Engineering & Reliability

### LinkedIn
https://www.linkedin.com/posts/team-mistral_aiengineering-dataagentbench-teammistral-activity-7448781849729912832-5IHf

### Medium
https://medium.com/p/e91af716c361?postPublishedType=initial

### X Thread
https://x.com/TsegayAsse64592/status/2045556572181410254?s=20

### Focus
- Context engineering as the key driver of reliability
- Reducing KB documents to <400 tokens
- Injection testing and system validation

---

## Post 4 — Final Benchmark & System Results

### LinkedIn
https://www.linkedin.com/feed/update/urn:li:activity:7451318313089028096

### X Thread
https://x.com/TsegayAsse64592/status/2045556572181410254?s=20

### Focus
- Final system performance (pass@1 improvement)
- Evaluation-driven development
- System design vs model performance

---

## Reddit Engagement

https://www.reddit.com/r/LocalLLaMA/comments/1skj9nm/building_a_data_agent_for_dataagentbench/

### Focus
- Context optimization
- Knowledge Base design
- Multi-database reasoning challenges

---

## Key Technical Themes Across Articles

- Context structure is more important than context size
- Join-key ambiguity is a major failure point in multi-database systems
- Injection testing is essential for Knowledge Base validation
- Evaluation-first development exposes real system weaknesses
- Correction loops (KB v3) improve system reliability over time

---

## Summary

Signal Corps articles and posts documented:

- Real system failures (not just successes)
- Engineering decisions and trade-offs
- Improvements from evaluation and iteration
- Insights that directly influenced system design

These outputs reflect active participation in the AI engineering community and contributed to improving the system itself.

