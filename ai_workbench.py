import ast
import datetime
import json
import operator
import os
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont
import urllib.request
import urllib.error
import webbrowser
from openai import OpenAI

# ==============================================================================
# TOOL IMPLEMENTATIONS
# ==============================================================================

def get_current_time() -> str:
    """Returns the current system date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_calculator(expression: str) -> str:
    """Safely evaluates basic arithmetic expressions without arbitrary code execution."""
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }

    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            return operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            return operators[type(node.op)](operand)
        raise ValueError(f"Unsupported syntax: {type(node).__name__}")

    try:
        clean_expr = expression.replace("^", "**")
        parsed = ast.parse(clean_expr, mode="eval")
        result = _eval(parsed.body)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"

def run_shell_command(command: str) -> str:
    """Runs a shell command with a 120s timeout window for longer compilations or tasks."""
    try:
        res = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = res.stdout if res.returncode == 0 else f"Stderr:\n{res.stderr}"
        return output.strip() if output.strip() else "[Command executed successfully with no output]"
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out after 120 seconds."
    except Exception as e:
        return f"Execution error: {str(e)}"

def read_local_file(filepath: str, max_chars: int = 12000) -> str:
    """Reads a local text file up to a maximum character threshold."""
    try:
        normalized_path = os.path.expanduser(filepath)
        if not os.path.exists(normalized_path):
            return f"Error: File '{filepath}' does not exist."
        with open(normalized_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
            truncated = " ... [Truncated]" if f.read(1) else ""
            return content + truncated
    except Exception as e:
        return f"File read error: {str(e)}"

def write_local_file(filepath: str, content: str) -> str:
    """Writes text content to a local file."""
    try:
        normalized_path = os.path.expanduser(filepath)
        parent_dir = os.path.dirname(os.path.abspath(normalized_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(normalized_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {filepath}."
    except Exception as e:
        return f"File write error: {str(e)}"

def get_system_info() -> str:
    """Collects operating system and hardware runtime information."""
    try:
        info = {
            "OS": platform.system(),
            "OS Release": platform.release(),
            "Architecture": platform.machine(),
            "Processor": platform.processor(),
            "CPU Cores (Logical)": os.cpu_count(),
            "Working Directory": os.getcwd(),
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"System info error: {str(e)}"

def huggingface_inference(model_id: str, inputs: str, hf_token: str = "") -> str:
    """Queries the Hugging Face Serverless Inference API with a 180-second timeout."""
    token = hf_token.strip() or os.environ.get("HF_TOKEN", "")
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "ImperialTekConsole/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = json.dumps({"inputs": inputs, "parameters": {"wait_for_model": True}}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return json.dumps(data, indent=2)[:4000]
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode("utf-8", errors="replace")
        return f"HF HTTP Error {err.code}: {err_msg[:400]}"
    except urllib.error.URLError as err:
        return f"HF Connection Timeout/Error: {str(err.reason)}"
    except Exception as e:
        return f"HF skill error: {str(e)}"

def toolchain_list_targets() -> str:
    """Queries 'toolchain list' via PowerShell to show all active and available targets."""
    cmd = 'powershell.exe -ExecutionPolicy Bypass -Command "toolchain list"'
    return run_shell_command(cmd)

def toolchain_dispatch_build(targets: list, payload_path: str, sign: bool = True, extra_flags: str = "") -> str:
    """Invokes toolchain to build, package, and optionally sign across targets."""
    targets_arg = ",".join(targets)
    sign_flag = "-Sign" if sign else ""
    cmd = (
        f'powershell.exe -ExecutionPolicy Bypass -Command '
        f'"toolchain -Targets {targets_arg} -Payload \'{payload_path}\' {sign_flag} {extra_flags}"'
    )
    return run_shell_command(cmd)

def toolchain_doctor_strict_json() -> str:
    """Executes 'toolchain doctor -Strict -Json' and returns structured diagnostic status."""
    cmd = 'powershell.exe -ExecutionPolicy Bypass -Command "toolchain doctor -Strict -Json"'
    raw_output = run_shell_command(cmd)
    try:
        parsed = json.loads(raw_output)
        return json.dumps(parsed, indent=2)
    except Exception:
        return raw_output.strip()

LOCAL_TOOL_REGISTRY = {
    "get_current_time": get_current_time,
    "calculator": safe_calculator,
    "run_shell_command": run_shell_command,
    "read_local_file": read_local_file,
    "write_local_file": write_local_file,
    "get_system_info": get_system_info,
    "huggingface_inference": huggingface_inference,
    "toolchain_list_targets": toolchain_list_targets,
    "toolchain_dispatch_build": toolchain_dispatch_build,
    "toolchain_doctor_strict_json": toolchain_doctor_strict_json,
}

# Risk classifications for permission gates
TOOL_RISK_MAP = {
    "get_current_time": "safe",
    "calculator": "safe",
    "get_system_info": "safe",
    "read_local_file": "safe",
    "toolchain_list_targets": "safe",
    "write_local_file": "moderate",
    "huggingface_inference": "moderate",
    "toolchain_doctor_strict_json": "moderate",
    "run_shell_command": "high",
    "toolchain_dispatch_build": "high",
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Fetch current date and time from the local machine.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Compute an arithmetic expression (supports +, -, *, /, **, %).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The math expression, e.g. '(14 * 1024) / 8'"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Run a local shell or terminal command (PowerShell, CMD, bash) to inspect systems, networks, or process files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command string to execute, e.g. 'dir' or 'ipconfig'"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_local_file",
            "description": "Inspect and read contents from a local file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative or absolute path to the target file."},
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_local_file",
            "description": "Create or overwrite a file on the local machine with new content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Target path to write the file."},
                    "content": {"type": "string", "description": "Raw string content to save into the file."},
                },
                "required": ["filepath", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Fetch machine specs including OS version, CPU counts, architecture, and current working directory.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "huggingface_inference",
            "description": "Query models hosted on Hugging Face Serverless Inference API for specialized tasks or embeddings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_id": {"type": "string", "description": "Repo ID on Hugging Face, e.g. 'bert-base-uncased'"},
                    "inputs": {"type": "string", "description": "Payload string sent to the model."},
                    "hf_token": {"type": "string", "description": "Optional Hugging Face user access token."},
                },
                "required": ["model_id", "inputs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toolchain_list_targets",
            "description": "List all discovered clients, bare-metal nodes, and virtualized targets (aarch64, macOS VM, Windows, Linux musl/glibc) and their active states.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toolchain_dispatch_build",
            "description": "Build, package, or sign payloads across one or multiple targets simultaneously.",
            "parameters": {
                "type": "object",
                "properties": {
                    "targets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target identifiers to compile for (e.g. ['bare_metal_aarch', 'macos_vm', 'linux_musl']) or ['all'].",
                    },
                    "payload_path": {
                        "type": "string",
                        "description": "Path to the script, directory, or artifact to compile.",
                    },
                    "sign": {
                        "type": "boolean",
                        "description": "Whether to run the signing pipeline on the output binaries.",
                    },
                    "extra_flags": {
                        "type": "string",
                        "description": "Optional flags forwarded directly to cross_systems_engine.py.",
                    },
                },
                "required": ["targets", "payload_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "toolchain_doctor_strict_json",
            "description": "Run the full matrix health verification using 'toolchain doctor -Strict -Json'. Returns machine-readable JSON detailing node status, compiler health, signatures, and linkers.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

# ==============================================================================
# MAIN APPLICATION GUI
# ==============================================================================

class UnifiedAIGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Imperial Tek Solutions - AI Console & Toolchain Workbench")
        self.geometry("1060x830")
        self.minsize(880, 640)
        self.configure(bg="#1e1e24")

        # Session state
        self.messages = []
        self.is_generating = False
        self.asked_save_config = False
        self.attached_file_path = None
        self.logo_img = None

        self.load_app_branding()
        self.setup_styles()
        self.build_menubar()
        self.build_layout()
        self.bind_shortcuts()

        self.load_config(silent=True)

    def load_app_branding(self):
        for icon_candidate in ["logo.png", "icon.png", "logo.ico", "icon.ico"]:
            if os.path.exists(icon_candidate):
                try:
                    if icon_candidate.endswith(".ico"):
                        self.iconbitmap(icon_candidate)
                    else:
                        img = tk.PhotoImage(file=icon_candidate)
                        self.iconphoto(True, img)
                    break
                except Exception:
                    pass

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background="#1e1e24")
        style.configure("Sidebar.TFrame", background="#16161a")
        style.configure("Status.TFrame", background="#16161a")

        style.configure("TLabel", background="#16161a", foreground="#94a1b2", font=("Segoe UI", 9))
        style.configure("BrandTitle.TLabel", background="#16161a", foreground="#fffffe", font=("Segoe UI", 11, "bold"))
        style.configure("BrandSub.TLabel", background="#16161a", foreground="#7f5af0", font=("Segoe UI", 8, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 9, "bold"), foreground="#94a1b2")
        style.configure("Value.TLabel", font=("Segoe UI", 8), foreground="#72757e")
        style.configure("Status.TLabel", background="#16161a", foreground="#94a1b2", font=("Segoe UI", 9))

        style.configure(
            "Action.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#7f5af0",
            foreground="#fffffe",
            borderwidth=0,
            padding=6,
        )
        style.map("Action.TButton", background=[("active", "#6e48e0"), ("disabled", "#383a47")])

        style.configure(
            "Control.TButton",
            font=("Segoe UI", 8),
            background="#242629",
            foreground="#fffffe",
            borderwidth=0,
            padding=4,
        )
        style.map("Control.TButton", background=[("active", "#33373b"), ("disabled", "#1b1c1e")])

    def build_menubar(self):
        menubar = tk.Menu(self, bg="#242629", fg="#fffffe", activebackground="#7f5af0")

        file_menu = tk.Menu(menubar, tearoff=0, bg="#16161a", fg="#fffffe")
        file_menu.add_command(label="Save Chat Log...", command=self.save_log)
        file_menu.add_command(label="Save Configuration", command=self.save_config)
        file_menu.add_command(label="Load Configuration", command=self.load_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0, bg="#16161a", fg="#fffffe")
        view_menu.add_command(label="Zoom In (Ctrl +)", command=lambda: self.zoom(1))
        view_menu.add_command(label="Zoom Out (Ctrl -)", command=lambda: self.zoom(-1))
        view_menu.add_command(label="Reset Zoom (Ctrl 0)", command=lambda: self.zoom(0))
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg="#16161a", fg="#fffffe")
        help_menu.add_command(label="About Imperial Tek Solutions", command=self.show_about_dialog)
        help_menu.add_command(label="Visit CodePolisher", command=lambda: webbrowser.open("https://codepolisher.app"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def build_layout(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ==================== LEFT SIDEBAR ====================
        sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding="14 14 14 14", width=300)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)
        sidebar.grid_propagate(False)

        # BRAND BANNER
        brand_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        brand_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        if os.path.exists("logo.png"):
            try:
                self.logo_img = tk.PhotoImage(file="logo.png")
                if self.logo_img.width() > 180:
                    ratio = int(self.logo_img.width() / 150) or 1
                    self.logo_img = self.logo_img.subsample(ratio, ratio)
                logo_lbl = tk.Label(brand_frame, image=self.logo_img, bg="#16161a")
                logo_lbl.pack(anchor="w", pady=(0, 4))
            except Exception:
                pass

        ttk.Label(brand_frame, text="IMPERIAL TEK", style="BrandTitle.TLabel").pack(anchor="w")
        ttk.Label(brand_frame, text="SOLUTIONS // AGENT ENGINE", style="BrandSub.TLabel").pack(anchor="w")

        ttk.Separator(sidebar, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=(4, 6))

        # SECURITY PERMISSION LEVEL (Low, Medium, High, Full)
        ttk.Label(sidebar, text="EXECUTION PERMISSIONS", style="Header.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.permission_var = tk.StringVar(value="Medium Access")
        perm_menu = ttk.Combobox(
            sidebar,
            textvariable=self.permission_var,
            values=["Low Access", "Medium Access", "High Access", "Full Access"],
            state="readonly",
        )
        perm_menu.grid(row=3, column=0, sticky="ew", pady=(2, 6))

        # Endpoint Configuration Section
        ttk.Label(sidebar, text="ENDPOINT CONFIG", style="Header.TLabel").grid(row=4, column=0, sticky="w", pady=(2, 2))

        # Presets
        ttk.Label(sidebar, text="Preset Provider:").grid(row=5, column=0, sticky="w")
        self.preset_var = tk.StringVar(value="OpenRouter")
        preset_box = ttk.Combobox(
            sidebar,
            textvariable=self.preset_var,
            values=["OpenRouter", "Venice AI", "Ollama (Local)", "OpenAI Custom"],
            state="readonly",
        )
        preset_box.grid(row=6, column=0, sticky="ew", pady=(2, 6))
        preset_box.bind("<<ComboboxSelected>>", self.apply_preset)

        # Base URL
        ttk.Label(sidebar, text="Base URL:").grid(row=7, column=0, sticky="w")
        self.base_url_entry = tk.Entry(sidebar, bg="#242629", fg="#fffffe", insertbackground="#fffffe", relief="flat")
        self.base_url_entry.grid(row=8, column=0, sticky="ew", pady=(2, 6), ipady=2)

        # API Key
        ttk.Label(sidebar, text="API Key:").grid(row=9, column=0, sticky="w")
        self.api_key_entry = tk.Entry(sidebar, bg="#242629", fg="#fffffe", insertbackground="#fffffe", relief="flat", show="*")
        self.api_key_entry.grid(row=10, column=0, sticky="ew", pady=(2, 6), ipady=2)

        # Model ID
        ttk.Label(sidebar, text="Model Identifier:").grid(row=11, column=0, sticky="w")
        self.model_entry = tk.Entry(sidebar, bg="#242629", fg="#fffffe", insertbackground="#fffffe", relief="flat")
        self.model_entry.grid(row=12, column=0, sticky="ew", pady=(2, 6), ipady=2)

        ttk.Separator(sidebar, orient="horizontal").grid(row=13, column=0, sticky="ew", pady=6)

        # Temperature
        temp_row = ttk.Frame(sidebar, style="Sidebar.TFrame")
        temp_row.grid(row=14, column=0, sticky="ew")
        ttk.Label(temp_row, text="Temperature:").pack(side="left")
        self.temp_val_lbl = ttk.Label(temp_row, text="0.20", style="Value.TLabel")
        self.temp_val_lbl.pack(side="right")

        self.temp_slider = ttk.Scale(sidebar, from_=0.0, to=1.5, value=0.2, command=self.update_temp_display)
        self.temp_slider.grid(row=15, column=0, sticky="ew", pady=(2, 6))

        # Max Tokens
        ttk.Label(sidebar, text="Max Tokens:").grid(row=16, column=0, sticky="w")
        self.tokens_entry = tk.Entry(sidebar, bg="#242629", fg="#fffffe", insertbackground="#fffffe", relief="flat")
        self.tokens_entry.grid(row=17, column=0, sticky="ew", pady=(2, 6), ipady=2)
        self.tokens_entry.insert(0, "4096")

        # System Prompt
        ttk.Label(sidebar, text="System Prompt:").grid(row=18, column=0, sticky="w")
        self.system_text = tk.Text(sidebar, bg="#242629", fg="#fffffe", insertbackground="#fffffe", relief="flat", height=4, wrap="word", font=("Segoe UI", 9))
        self.system_text.grid(row=19, column=0, sticky="ew", pady=(2, 6))
        default_prompt = (
            "You are an autonomous engineering assistant managing a multi-target cross-compilation matrix.\n"
            "MANDATORY DIRECTIVE: Whenever you write, modify, implement, or dispatch code across the targets, "
            "you MUST immediately execute toolchain_doctor_strict_json. Inspect the JSON to verify that all nodes, "
            "linkers, and signing keys are clean before concluding your task."
        )
        self.system_text.insert("1.0", default_prompt)

        # Sidebar Buttons
        btn_box = ttk.Frame(sidebar, style="Sidebar.TFrame")
        btn_box.grid(row=20, column=0, sticky="ew", pady=(6, 0))
        btn_box.columnconfigure(0, weight=1)
        btn_box.columnconfigure(1, weight=1)

        clear_btn = tk.Button(btn_box, text="Clear Chat", bg="#242629", fg="#ff5470", relief="flat", command=self.clear_chat)
        clear_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=3)

        save_cfg_btn = tk.Button(btn_box, text="Save Config", bg="#242629", fg="#2cb67d", relief="flat", command=self.save_config)
        save_cfg_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), ipady=3)

        self.apply_preset()

        # ==================== RIGHT CHAT WORKBENCH ====================
        content = ttk.Frame(self, style="TFrame", padding="12 12 12 12")
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # Output History
        history_frame = ttk.Frame(content, style="TFrame")
        history_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        self.chat_history = tk.Text(
            history_frame,
            bg="#242629",
            fg="#fffffe",
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            padx=12,
            pady=12,
        )
        self.chat_history.grid(row=0, column=0, sticky="nsew")

        history_scroll = ttk.Scrollbar(history_frame, orient="vertical", command=self.chat_history.yview)
        self.chat_history.configure(yscrollcommand=history_scroll.set)
        history_scroll.grid(row=0, column=1, sticky="ns")

        # Color Tags
        self.chat_history.tag_configure("user", foreground="#2cb67d", font=("Consolas", 10, "bold"))
        self.chat_history.tag_configure("assistant", foreground="#7f5af0", font=("Consolas", 10, "bold"))
        self.chat_history.tag_configure("tool", foreground="#f5a623", font=("Consolas", 9, "bold"))
        self.chat_history.tag_configure("tool_out", foreground="#94a1b2", font=("Consolas", 9))
        self.chat_history.tag_configure("blocked", foreground="#ff5470", font=("Consolas", 9, "bold"))
        self.chat_history.tag_configure("error", foreground="#ff5470", font=("Consolas", 10, "bold"))

        # Input & File Attachment Container
        input_container = ttk.Frame(content, style="TFrame")
        input_container.grid(row=1, column=0, sticky="ew")
        input_container.columnconfigure(0, weight=1)

        # File Attachment Header Bar
        attach_bar = ttk.Frame(input_container, style="TFrame")
        attach_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        
        self.attach_btn = tk.Button(
            attach_bar,
            text="[+] Attach File",
            bg="#242629",
            fg="#7f5af0",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            command=self.select_file_attachment,
        )
        self.attach_btn.pack(side="left")

        self.attached_label = tk.Label(
            attach_bar,
            text="No file attached",
            bg="#1e1e24",
            fg="#72757e",
            font=("Segoe UI", 8),
        )
        self.attached_label.pack(side="left", padx=(8, 0))

        self.clear_file_btn = tk.Button(
            attach_bar,
            text="✕",
            bg="#1e1e24",
            fg="#ff5470",
            relief="flat",
            font=("Segoe UI", 8, "bold"),
            command=self.clear_file_attachment,
        )

        # Prompt Input Box
        self.user_input = tk.Text(
            input_container,
            bg="#242629",
            fg="#fffffe",
            insertbackground="#fffffe",
            relief="flat",
            height=3,
            font=("Segoe UI", 10),
            wrap="word",
            padx=8,
            pady=8,
        )
        self.user_input.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        # Action Buttons Column
        action_col = ttk.Frame(input_container, style="TFrame")
        action_col.grid(row=1, column=1, sticky="ns")

        self.send_button = ttk.Button(action_col, text="Send ↵", style="Action.TButton", command=self.submit_prompt)
        self.send_button.pack(fill="x", expand=True, pady=(0, 4))

        self.stop_button = ttk.Button(action_col, text="■ Stop", style="Control.TButton", command=self.stop_generation, state="disabled")
        self.stop_button.pack(fill="x", expand=True, pady=(0, 4))

        self.copy_button = ttk.Button(action_col, text="Copy Last", style="Control.TButton", command=self.copy_last_response)
        self.copy_button.pack(fill="x", expand=True)

        # ==================== BOTTOM STATUS BAR ====================
        status_bar = ttk.Frame(self, style="Status.TFrame", padding="6 4 10 4")
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_var = tk.StringVar(value="Ready // Imperial Tek Solutions")
        ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel").pack(side="left")

        self.token_label = ttk.Label(status_bar, text="Tokens (est): 0", style="Status.TLabel")
        self.token_label.pack(side="right")

    def bind_shortcuts(self):
        self.bind("<Control-plus>", lambda e: self.zoom(1))
        self.bind("<Control-equal>", lambda e: self.zoom(1))
        self.bind("<Control-minus>", lambda e: self.zoom(-1))
        self.bind("<Control-0>", lambda e: self.zoom(0))
        self.user_input.bind("<Return>", self.handle_key_enter)

    # ==============================================================================
    # APPROVAL MODAL & PERMISSION GATE ENGINE
    # ==============================================================================

    def requires_approval(self, fn_name: str) -> bool:
        """Determines if a tool call requires explicit human approval based on permission level."""
        level = self.permission_var.get()
        risk = TOOL_RISK_MAP.get(fn_name, "high")

        if level == "Full Access":
            return False
        elif level == "High Access":
            return risk == "high"
        elif level == "Medium Access":
            return risk in ["moderate", "high"]
        elif level == "Low Access":
            return True  # Guard all executions
        return True

    def request_tool_approval(self, fn_name: str, raw_args: str) -> bool:
        """Pops a clean dark-themed modal prompting the user to Approve or Reject the tool call."""
        result_container = {"approved": False}
        wait_event = threading.Event()

        def _ask_ui():
            dialog = tk.Toplevel(self)
            dialog.title("Authorization Required")
            dialog.geometry("520x360")
            dialog.minsize(480, 320)
            dialog.configure(bg="#16161a")
            dialog.transient(self)
            dialog.grab_set()

            p = tk.Frame(dialog, bg="#16161a", padx=20, pady=20)
            p.pack(fill="both", expand=True)

            tk.Label(
                p,
                text="TOOL EXECUTION GATE",
                font=("Segoe UI", 11, "bold"),
                fg="#f5a623",
                bg="#16161a",
            ).pack(anchor="w")

            perm_desc = f"Security Tier: {self.permission_var.get()}  |  Risk Level: {TOOL_RISK_MAP.get(fn_name, 'high').upper()}"
            tk.Label(p, text=perm_desc, font=("Segoe UI", 8), fg="#94a1b2", bg="#16161a").pack(anchor="w", pady=(2, 10))

            tk.Label(p, text=f"Target Tool: {fn_name}", font=("Segoe UI", 10, "bold"), fg="#fffffe", bg="#16161a").pack(anchor="w")

            tk.Label(p, text="Incoming Parameters:", font=("Segoe UI", 8), fg="#94a1b2", bg="#16161a").pack(anchor="w", pady=(8, 2))
            
            box = tk.Text(p, bg="#242629", fg="#fffffe", relief="flat", font=("Consolas", 9), height=7, wrap="word")
            box.pack(fill="both", expand=True)
            box.insert("1.0", raw_args)
            box.config(state="disabled")

            btn_box = tk.Frame(p, bg="#16161a")
            btn_box.pack(fill="x", pady=(15, 0))

            def _approve():
                result_container["approved"] = True
                dialog.destroy()
                wait_event.set()

            def _reject():
                result_container["approved"] = False
                dialog.destroy()
                wait_event.set()

            dialog.protocol("WM_DELETE_WINDOW", _reject)

            reject_btn = tk.Button(
                btn_box,
                text="Reject ✕",
                bg="#242629",
                fg="#ff5470",
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                padx=15,
                pady=6,
                command=_reject,
            )
            reject_btn.pack(side="left")

            approve_btn = tk.Button(
                btn_box,
                text="Approve ✓",
                bg="#7f5af0",
                fg="#fffffe",
                relief="flat",
                font=("Segoe UI", 9, "bold"),
                padx=20,
                pady=6,
                command=_approve,
            )
            approve_btn.pack(side="right")

        # Schedule dialog on main GUI thread and wait for choice
        self.after(0, _ask_ui)
        wait_event.wait()
        return result_container["approved"]

    # ==============================================================================
    # CUSTOM BRANDED ABOUT DIALOG
    # ==============================================================================

    def show_about_dialog(self):
        about_win = tk.Toplevel(self)
        about_win.title("About Imperial Tek Solutions")
        about_win.geometry("520x420")
        about_win.minsize(480, 380)
        about_win.configure(bg="#16161a")
        about_win.transient(self)
        about_win.grab_set()

        content = tk.Frame(about_win, bg="#16161a", padx=25, pady=20)
        content.pack(fill="both", expand=True)

        header_frame = tk.Frame(content, bg="#16161a")
        header_frame.pack(fill="x", pady=(0, 10))

        if self.logo_img:
            logo_sub = tk.Label(header_frame, image=self.logo_img, bg="#16161a")
            logo_sub.pack(side="left", padx=(0, 15))

        title_box = tk.Frame(header_frame, bg="#16161a")
        title_box.pack(side="left", fill="y")
        tk.Label(title_box, text="IMPERIAL TEK SOLUTIONS", font=("Segoe UI", 13, "bold"), fg="#fffffe", bg="#16161a").pack(anchor="w")
        tk.Label(title_box, text="Universal Toolchain & AI Systems", font=("Segoe UI", 9, "bold"), fg="#7f5af0", bg="#16161a").pack(anchor="w")

        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=10)

        desc_text = (
            "Specialized engineering solutions for multi-target cross-compilation, "
            "headless binary signing, local execution matrices, and autonomous LLM agents."
        )
        tk.Label(content, text=desc_text, font=("Segoe UI", 9), fg="#94a1b2", bg="#16161a", wraplength=460, justify="left").pack(anchor="w", pady=(0, 15))

        tk.Label(content, text="FLAGSHIP PLATFORMS & REPOSITORIES", font=("Segoe UI", 9, "bold"), fg="#fffffe", bg="#16161a").pack(anchor="w", pady=(0, 6))

        def create_link(parent, label_text, url):
            f = tk.Frame(parent, bg="#16161a")
            f.pack(fill="x", pady=2)
            tk.Label(f, text=label_text, font=("Segoe UI", 9), fg="#94a1b2", bg="#16161a", width=14, anchor="w").pack(side="left")
            link_lbl = tk.Label(f, text=url, font=("Segoe UI", 9, "underline"), fg="#2cb67d", bg="#16161a", cursor="hand2")
            link_lbl.pack(side="left")
            link_lbl.bind("<Button-1>", lambda e: webbrowser.open(url if "://" in url or "@" not in url else f"mailto:{url}"))

        create_link(content, "CodePolisher:", "https://codepolisher.app")
        create_link(content, "GitHub:", "https://github.com/v1ral-its")
        create_link(content, "Contact / PM:", "itsolutions_mgnt@pm.me")

        ttk.Separator(content, orient="horizontal").pack(fill="x", pady=(15, 10))

        close_btn = tk.Button(
            content,
            text="Close",
            bg="#242629",
            fg="#fffffe",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=15,
            pady=4,
            command=about_win.destroy,
        )
        close_btn.pack(side="right")

    # ==============================================================================
    # FILE ATTACHMENT HANDLING
    # ==============================================================================

    def select_file_attachment(self):
        file_path = filedialog.askopenfilename(
            title="Select File to Attach",
            filetypes=[("All Files", "*.*"), ("Text / Code", "*.txt;*.py;*.json;*.md;*.ps1;*.sh;*.js")],
        )
        if file_path:
            self.attached_file_path = file_path
            filename = os.path.basename(file_path)
            size_kb = os.path.getsize(file_path) / 1024
            self.attached_label.config(text=f"Attached: {filename} ({size_kb:.1f} KB)", fg="#2cb67d")
            self.clear_file_btn.pack(side="left", padx=(4, 0))

    def clear_file_attachment(self):
        self.attached_file_path = None
        self.attached_label.config(text="No file attached", fg="#72757e")
        self.clear_file_btn.pack_forget()

    # ==============================================================================
    # EVENT HANDLERS & AGENT DISPATCH
    # ==============================================================================

    def update_temp_display(self, val):
        self.temp_val_lbl.config(text=f"{float(val):.2f}")

    def apply_preset(self, event=None):
        preset = self.preset_var.get()
        self.base_url_entry.delete(0, tk.END)
        self.model_entry.delete(0, tk.END)

        if preset == "OpenRouter":
            self.base_url_entry.insert(0, "https://openrouter.ai/api/v1")
            self.model_entry.insert(0, "nvidia/llama-3.1-nemotron-70b-instruct")
        elif preset == "Venice AI":
            self.base_url_entry.insert(0, "https://api.venice.ai/api/v1")
            self.model_entry.insert(0, "llama-3.3-70b")
        elif preset == "Ollama (Local)":
            self.base_url_entry.insert(0, "http://localhost:11434/v1")
            self.model_entry.insert(0, "llama3:latest")
            if not self.api_key_entry.get():
                self.api_key_entry.insert(0, "ollama")
        elif preset == "OpenAI Custom":
            self.base_url_entry.insert(0, "https://api.openai.com/v1")
            self.model_entry.insert(0, "gpt-4o")

    def log_text(self, text, tag=None):
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", text, tag)
        self.chat_history.see("end")
        self.chat_history.config(state="disabled")

    def handle_key_enter(self, event):
        if not (event.state & 0x0001):
            self.submit_prompt()
            return "break"

    def clear_chat(self):
        self.messages.clear()
        self.chat_history.config(state="normal")
        self.chat_history.delete("1.0", tk.END)
        self.chat_history.config(state="disabled")
        self.update_token_count()
        self.status_var.set("Context cleared.")

    def submit_prompt(self):
        prompt = self.user_input.get("1.0", "end-1c").strip()
        if not prompt and not self.attached_file_path:
            return
        if self.is_generating:
            return

        base_url = self.base_url_entry.get().strip()
        api_key = self.api_key_entry.get().strip()
        model = self.model_entry.get().strip()

        if not base_url or not model:
            messagebox.showerror("Error", "Base URL and Model ID are mandatory.")
            return

        if not self.messages:
            system_instruction = self.system_text.get("1.0", tk.END).strip()
            if system_instruction:
                self.messages.append({"role": "system", "content": system_instruction})

        full_user_content = prompt
        if self.attached_file_path:
            file_meta = f"\n[Attached File: {os.path.basename(self.attached_file_path)}]\n"
            try:
                with open(self.attached_file_path, "r", encoding="utf-8", errors="replace") as f:
                    file_body = f.read(15000)
                    truncated_flag = " ... [Truncated]" if f.read(1) else ""
                full_user_content = f"{prompt}\n\n```\n{file_meta}{file_body}{truncated_flag}\n```"
            except Exception as e:
                full_user_content = f"{prompt}\n\n[Failed to read attached file: {str(e)}]"
            
            self.clear_file_attachment()

        self.messages.append({"role": "user", "content": full_user_content})
        self.log_text("You: ", "user")
        self.log_text(f"{full_user_content}\n\n")
        self.user_input.delete("1.0", "end")

        self.is_generating = True
        self.send_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_var.set("Generating / Invoking Agent...")

        threading.Thread(
            target=self.agent_worker_loop,
            args=(base_url, api_key, model),
            daemon=True,
        ).start()

    def stop_generation(self):
        self.is_generating = False
        self.stop_button.config(state="disabled")
        self.status_var.set("Execution cancelled by user.")

    def agent_worker_loop(self, base_url, api_key, model):
        try:
            client = OpenAI(base_url=base_url, api_key=api_key or "sk-dummy")
            max_turns = 12

            while max_turns > 0 and self.is_generating:
                max_turns -= 1
                temperature = round(float(self.temp_slider.get()), 2)
                max_tok_val = self.tokens_entry.get().strip()
                max_tokens = int(max_tok_val) if max_tok_val.isdigit() and int(max_tok_val) > 0 else None

                response = client.chat.completions.create(
                    model=model,
                    messages=self.messages,
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                response_msg = response.choices[0].message
                self.messages.append(response_msg)

                if response_msg.tool_calls:
                    for tool_call in response_msg.tool_calls:
                        if not self.is_generating:
                            break

                        fn_name = tool_call.function.name
                        raw_args = tool_call.function.arguments
                        tool_call_id = tool_call.id

                        self.after(0, self.log_text, f"[Tool Invoked]: {fn_name}({raw_args})\n", "tool")

                        # PERMISSION CHECK GATE
                        if self.requires_approval(fn_name):
                            self.after(0, self.status_var.set, f"Waiting for approval: {fn_name}...")
                            approved = self.request_tool_approval(fn_name, raw_args)
                            if not approved:
                                result = f"Execution Denied: User rejected permission to run '{fn_name}'."
                                self.after(0, self.log_text, f"[Action Blocked]: User rejected tool execution.\n\n", "blocked")
                                self.messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "name": fn_name,
                                    "content": str(result),
                                })
                                continue

                        # EXECUTE APPROVED TOOL
                        if fn_name in LOCAL_TOOL_REGISTRY:
                            try:
                                args_dict = json.loads(raw_args) if raw_args else {}
                                result = LOCAL_TOOL_REGISTRY[fn_name](**args_dict)
                            except Exception as ex:
                                result = f"Tool execution failed: {str(ex)}"
                        else:
                            result = f"Error: Function '{fn_name}' is not in the registry."

                        preview = str(result).strip()
                        if len(preview) > 400:
                            preview = preview[:400] + " ... [Output Trimmed]"
                        self.after(0, self.log_text, f"[Result]: {preview}\n\n", "tool_out")

                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": fn_name,
                            "content": str(result),
                        })

                    continue

                if response_msg.content:
                    self.after(0, self.log_text, "Assistant: ", "assistant")
                    self.after(0, self.log_text, f"{response_msg.content}\n\n")
                    break

        except Exception as e:
            self.after(0, self.log_text, f"\n[API Error: {str(e)}]\n\n", "error")
        finally:
            self.after(0, self.finalize_turn)

    def finalize_turn(self):
        self.is_generating = False
        self.stop_button.config(state="disabled")
        self.send_button.config(state="normal")
        self.status_var.set("Ready // Imperial Tek Solutions")
        self.update_token_count()

        if not self.asked_save_config:
            self.asked_save_config = True
            if messagebox.askyesno("Save Configuration", "Save these endpoint credentials to chat_config.json for next launch?"):
                self.save_config()

    def copy_last_response(self):
        for msg in reversed(self.messages):
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)

            if role == "assistant" and content:
                self.clipboard_clear()
                self.clipboard_append(content)
                self.status_var.set("Copied response to clipboard.")
                return
        self.status_var.set("No assistant content to copy.")

    def update_token_count(self):
        total_chars = 0
        for msg in self.messages:
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            if content:
                total_chars += len(str(content))
        self.token_label.config(text=f"Tokens (est): {total_chars // 4}")

    def zoom(self, direction):
        font_obj = tkfont.nametofont(self.chat_history.cget("font"))
        size = font_obj.cget("size")
        new_size = 10 if direction == 0 else max(8, min(24, size + direction))
        font_obj.configure(size=new_size)

    def save_config(self):
        config = {
            "base_url": self.base_url_entry.get().strip(),
            "api_key": self.api_key_entry.get().strip(),
            "model": self.model_entry.get().strip(),
            "temperature": self.temp_slider.get(),
            "max_tokens": self.tokens_entry.get().strip(),
            "permissions": self.permission_var.get(),
            "system_prompt": self.system_text.get("1.0", "end-1c").strip(),
        }
        try:
            with open("chat_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            self.status_var.set("Configuration saved to chat_config.json")
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not write config:\n{e}")

    def load_config(self, silent=False):
        if not os.path.exists("chat_config.json"):
            if not silent:
                messagebox.showinfo("Not Found", "No chat_config.json found.")
            return
        try:
            with open("chat_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            self.base_url_entry.delete(0, tk.END)
            self.base_url_entry.insert(0, config.get("base_url", ""))
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, config.get("api_key", ""))
            self.model_entry.delete(0, tk.END)
            self.model_entry.insert(0, config.get("model", ""))
            self.temp_slider.set(config.get("temperature", 0.2))
            self.update_temp_display(config.get("temperature", 0.2))
            self.tokens_entry.delete(0, tk.END)
            self.tokens_entry.insert(0, config.get("max_tokens", "4096"))
            if "permissions" in config:
                self.permission_var.set(config.get("permissions", "Medium Access"))
            if "system_prompt" in config:
                self.system_text.delete("1.0", tk.END)
                self.system_text.insert("1.0", config.get("system_prompt"))
            if not silent:
                self.status_var.set("Configuration loaded successfully.")
        except Exception as e:
            if not silent:
                messagebox.showerror("Load Error", f"Could not read config:\n{e}")

    def save_log(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Log", "*.txt"), ("Markdown File", "*.md"), ("All Files", "*.*")],
            title="Export Chat Log",
        )
        if not filepath:
            return
        try:
            content = self.chat_history.get("1.0", "end-1c")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_var.set(f"Log exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export log:\n{e}")


if __name__ == "__main__":
    app = UnifiedAIGUI()
    app.mainloop()

