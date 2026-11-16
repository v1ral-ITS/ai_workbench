<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0b0c10,45:6366f1,100:41d9ff&height=210&section=header&text=ITS%20AI%20Workbench&fontSize=48&fontColor=ffffff&fontAlignY=34&desc=Your%20model.%20Your%20machine.%20Your%20permissions.&descAlignY=58&descSize=15" width="100%" alt="ITS AI Workbench — ImPerial TeK. Solutions" />

[![Python](https://img.shields.io/badge/python-3.x-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-33d18b?style=for-the-badge)](LICENSE)
[![GUI](https://img.shields.io/badge/interface-Tkinter-8067ff?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![OpenAI compatible](https://img.shields.io/badge/endpoints-OpenAI--compatible-41d9ff?style=for-the-badge)](https://platform.openai.com/docs/api-reference)

**A portable, operator-controlled front end for local and hosted AI agents.**

Built by **Bear Carrington · ImPerial TeK. Solutions**

[Landing page](https://its-ai-workbench.coiledbiscuit8.chatgpt.site) · [CodePolisher](https://codepolisher.app) · [ITS-Convert](https://github.com/v1ral-ITS/ITS-Convert)

<img width="1066" height="892" alt="ITS AI Workbench interface" src="https://github.com/user-attachments/assets/b44d2c55-c039-46de-9525-9302b40ab30e" />

</div>

---

## What this is

ITS AI Workbench is a single-file Python GUI for connecting an OpenAI-compatible model endpoint to real local workflows.

It is deliberately small and inspectable. The model can be local or hosted; the endpoint can be Ollama, OpenRouter, Venice AI, OpenAI, or another compatible service; and the operator chooses which local tools the agent is allowed to invoke.

The important boundary is visible:

> The model proposes a tool call. Workbench displays it, classifies its risk, applies the selected permission tier, and records the result.

This is not a claim that one script replaces an entire model runtime. It is the control layer that makes a capable runtime useful at the desktop.

## Why it matters

A lot of software hides the difficult part behind a large application shell. This project shows the opposite approach: a small amount of Python can connect serious models to files, diagnostics, shell commands, Hugging Face inference, and a cross-platform build system—while keeping the execution decision in front of the person operating the machine.

That makes Workbench a natural companion to a local `llama.cpp` build with Vulkan, OpenVINO, or another runtime that exposes an OpenAI-compatible endpoint. The runtime determines which models your hardware can serve. Workbench gives you one consistent operator interface above it.

## Capabilities

| Capability | What it does |
|---|---|
| Provider presets | OpenRouter, Venice AI, Ollama (local), and OpenAI Custom |
| Model freedom | Connect any model your selected runtime or provider can serve, from small local models to hosted large models |
| Visible agent loop | Shows assistant messages, tool calls, tool results, blocks, and errors in the chat history |
| Permission tiers | Low, Medium, High, and Full Access gates based on tool risk |
| Local file workflow | Attach files, read approved local files, and write approved local files |
| System operations | Run shell commands, inspect system information, and query the Universal Toolchain |
| Long-running work | Background worker loop with a visible Stop control and a maximum of 12 agent turns |
| Portability | Python + Tkinter GUI with no hosted application account required |
| Session portability | Save endpoint configuration and export chat logs |

## Permission model

Tools are classified as `safe`, `moderate`, or `high` risk.

| Selected tier | Approval behavior |
|---|---|
| **Low Access** | Every tool call requires explicit approval |
| **Medium Access** | Moderate and high-risk calls require approval |
| **High Access** | Only high-risk calls require approval |
| **Full Access** | Tool calls run without the approval modal |

Full Access is intentionally powerful. If a tool is allowed to run a shell command or write a file, it can act with the operating-system permissions of the Workbench process. Do not give untrusted prompts or models unrestricted access to a machine you care about.

## Registered tools

The current tool registry includes:

| Tool | Risk | Purpose |
|---|---:|---|
| `get_current_time` | safe | Read the local date and time |
| `calculator` | safe | Evaluate basic arithmetic through a restricted AST |
| `get_system_info` | safe | Return OS, architecture, processor, cores, and working directory |
| `read_local_file` | safe | Read a local text file with a character limit |
| `toolchain_list_targets` | safe | List targets discovered by the Universal Toolchain |
| `write_local_file` | moderate | Create or overwrite a local text file |
| `huggingface_inference` | moderate | Query Hugging Face Serverless Inference |
| `toolchain_doctor_strict_json` | moderate | Run strict, machine-readable toolchain diagnostics |
| `run_shell_command` | high | Run a local shell command with a 120-second timeout |
| `toolchain_dispatch_build` | high | Dispatch build, package, and optional signing work across targets |

The registry is ordinary Python. Read it. Change it. Add the tool you actually need. Keep the risk classification honest.

## Architecture

```text
┌──────────────────────────────┐
│        Tkinter GUI           │
│  endpoint · model · access   │
└──────────────┬───────────────┘
               │ OpenAI-compatible API
┌──────────────▼───────────────┐
│       Selected runtime       │
│ Ollama · llama.cpp · hosted  │
└──────────────┬───────────────┘
               │ model proposes tool calls
┌──────────────▼───────────────┐
│     Workbench agent loop     │
│ visible calls · risk gate    │
└──────────────┬───────────────┘
               │ approved local actions
┌──────────────▼───────────────┐
│ files · shell · HF · builds  │
└──────────────────────────────┘
```

Workbench does not care whether the endpoint is backed by a small quantized model, a large local model, or a hosted model. It cares that the endpoint speaks the expected API shape and that the operator can see what the agent is asking to do.

## Install

Requirements:

- Python 3.x
- Tkinter, normally included with desktop Python installations
- The OpenAI Python client

Windows PowerShell:

```powershell
git clone https://github.com/v1ral-ITS/ai_workbench
cd ai_workbench
python -m pip install openai
python ai_workbench.py
```

Linux/macOS:

```bash
git clone https://github.com/v1ral-ITS/ai_workbench
cd ai_workbench
python3 -m pip install openai
python3 ai_workbench.py
```

## Connect a local llama.cpp or Vulkan runtime

If your local runtime exposes an OpenAI-compatible server, select **OpenAI Custom** or enter the endpoint manually.

Example endpoint shape:

```text
Base URL:  http://127.0.0.1:11434/v1
API key:   local-runtime
Model ID:  the-model-name-served-by-your-runtime
```

The exact port, model identifier, context size, Vulkan backend, quantization, and launch flags belong to the runtime you built. Workbench is intentionally endpoint-agnostic: it can sit above a custom `llama.cpp` Vulkan build just as easily as it can sit above Ollama or a hosted provider.

## The cost story

Workbench keeps hosted API spending optional:

- A local endpoint can run without a hosted API bill.
- Hosted providers may offer free tiers, introductory access, or inexpensive model options.
- Provider pricing, limits, and availability can change; no provider's free tier should be treated as a permanent guarantee.
- Large models still require real compute somewhere. “Free to call” is not the same as “free to run.”

That is the honest advantage: one interface, many backends, and no forced provider lock-in.

## Security notes

- `chat_config.json` can contain the API key entered in the GUI. Treat it as a secret and protect or remove it before sharing the directory.
- Hosted endpoints receive whatever prompt and attached content you send to them.
- File and shell tools are not a sandbox. They operate within the permissions of the Python process.
- Start with **Medium Access** or **Low Access** while testing a new model or system prompt.
- Review generated changes and run tests. An AI response is not proof that a command or build is correct.

## Relationship to the ITS toolchain

This project is one layer in the ImPerial TeK. Solutions stack:

- **ITS AI Workbench** — connect models to visible, permission-aware local workflows.
- **CodePolisher** — review code for quality, security, performance, and readability.
- **ITS-Convert** — translate and package automation scripts across languages and platforms.
- **Universal Toolchain** — inspect, build, package, sign, and validate multi-target outputs.

Together, they form a practical route from model-assisted reasoning to reviewed, translated, and reproducible artifacts.

## License

MIT — see [LICENSE](LICENSE).

<div align="center">

**ImPerial TeK. Solutions · Tools that keep your workflow under your control.**

[Explore the GitHub](https://github.com/v1ral-ITS) · [Try CodePolisher](https://codepolisher.app)

</div>
