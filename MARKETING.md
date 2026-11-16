# ITS AI Workbench — Marketing Kit

## Product identity

**Product:** ITS AI Workbench  
**Category:** Portable, operator-controlled AI workbench  
**Tagline:** Your model. Your machine. Your permissions.

### One-line description

A one-file Python GUI that connects any OpenAI-compatible model endpoint—from a custom `llama.cpp`/Vulkan runtime to hosted providers—to real local tools with visible, risk-gated permissions.

### Short pitch

ITS AI Workbench puts a serious model beside the work instead of hiding it behind a hosted application. Choose the endpoint, choose the model, choose the tools, and choose how much authority the agent receives.

## The three product pillars

1. **Model freedom**  
   Use a local runtime, OpenRouter, Venice AI, OpenAI, or another compatible endpoint. The model can change without replacing the operator interface.

2. **Visible agency**  
   Tool calls, parameters, results, blocks, and errors stay in the conversation. The operator can see what the agent is trying to do.

3. **Explicit authority**  
   Low, Medium, High, and Full Access tiers make execution policy a visible choice. Full Access is powerful and should be treated as a deliberate trust decision.

## Who it is for

- Local-model builders and `llama.cpp`/Vulkan experimenters
- Developers and DevOps engineers who want an AI beside their files and build systems
- Students learning how model APIs, tools, operating systems, and automation fit together
- People who want hosted inference to remain optional rather than mandatory

## The honest cost message

Local inference can avoid a hosted API bill. Providers may offer free tiers or introductory access, but their limits and pricing can change. Large models still require real compute somewhere. The durable benefit is backend freedom and one consistent interface—not a promise of permanently free hosted inference.

## Launch copy

### GitHub release blurb

> Introducing ITS AI Workbench: a portable Python GUI for connecting local or hosted AI models to real workflows. It supports OpenAI-compatible endpoints, visible tool calls, Low/Medium/High/Full permission tiers, local file operations, shell commands, Hugging Face inference, and Universal Toolchain diagnostics. Pair it with a custom `llama.cpp` Vulkan build, Ollama, OpenRouter, or another compatible runtime. One file, inspectable code, and the operator stays in the loop.

### Social post

> People keep asking AI to “use the computer” while hiding the part that matters: what it is allowed to do.
>
> I built ITS AI Workbench as a small, inspectable Python GUI that connects serious models to real files, shell commands, diagnostics, Hugging Face, and my Universal Toolchain.
>
> Your model. Your machine. Your permissions.
>
> Local runtime or hosted endpoint. Low access or full access. Visible tool calls. A stop control. No forced provider lock-in.
>
> https://github.com/v1ral-ITS/ai_workbench

## Positioning guardrails

Say:

- “Any model your selected runtime or provider can serve.”
- “Hosted API spending remains optional.”
- “Full Access uses the operating-system permissions of the Python process.”
- “The tool-call boundary is visible and operator-controlled.”

Do not say:

- “Every model runs on every computer.”
- “All providers are permanently free.”
- “The permission tiers are a security sandbox.”
- “AI output is automatically correct.”

## Product family

- **ITS AI Workbench:** connect models to controlled local workflows.
- **CodePolisher:** review code for quality, security, performance, and readability.
- **ITS-Convert:** translate and package scripts across languages and platforms.
- **Universal Toolchain:** inspect, build, package, sign, and validate multi-target artifacts.

The family story is simple: reason, review, translate, build.
