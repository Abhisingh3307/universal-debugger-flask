from flask import Flask, request, render_template
import subprocess, os, tempfile, re

app = Flask(__name__)

LANG_COMMANDS = {
    "python": {"ext": ".py", "run": lambda f: ["python", f]},
    "cpp": {"ext": ".cpp", "run": lambda f: ["bash", "-c", f"g++ {f} -o temp_out && ./temp_out"]},
    "java": {"ext": ".java", "run": lambda f: ["bash", "-c", f"javac {f} && java {os.path.splitext(os.path.basename(f))[0]}"]},
    "bash": {"ext": ".sh", "run": lambda f: ["bash", f]},
    "node": {"ext": ".js", "run": lambda f: ["node", f]}
}

def detect_language(code):
    if "import java" in code or "public static void main" in code: return "java"
    if "#include" in code and "int main" in code: return "cpp"
    if "console.log" in code or "function(" in code: return "node"
    if "def " in code or "import " in code: return "python"
    if code.strip().startswith("echo") or "#!/bin/bash" in code: return "bash"
    return "unknown"

def run_code(code):
    lang = detect_language(code)
    if lang not in LANG_COMMANDS:
        return "", f"Unsupported language: {lang}", "FAILED"

    ext = LANG_COMMANDS[lang]["ext"]
    run_cmd = LANG_COMMANDS[lang]["run"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode="w") as temp:
        temp.write(code)
        temp_path = temp.name

    try:
        process = subprocess.run(run_cmd(temp_path), capture_output=True, text=True, timeout=10)
        stdout = process.stdout.strip() or "(No Output)"
        stderr = process.stderr.strip() or "(No Errors)"
        status = "PASSED" if process.returncode == 0 else "FAILED"
    except subprocess.TimeoutExpired:
        stdout, stderr, status = "(No Output)", "Execution timed out.", "FAILED"
    except Exception as e:
        stdout, stderr, status = "(No Output)", str(e), "FAILED"
    finally:
        try:
            os.remove(temp_path)
            if lang == "cpp" and os.path.exists("temp_out"):
                os.remove("temp_out")
        except:
            pass

    return stdout, stderr, status

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        code = request.form["code"]
        stdout, stderr, status = run_code(code)
        return render_template("index.html", code=code, stdout=stdout, stderr=stderr, status=status)
    return render_template("index.html", code="", stdout="", stderr="", status="")

if __name__ == "__main__":
    app.run(debug=True)
      
