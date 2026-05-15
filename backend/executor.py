import os
import subprocess
import tempfile
import shutil

try:
    import resource
except ImportError:
    resource = None

from languages import get_language

COMPILE_TIMEOUT = 10
EXECUTION_TIMEOUT = 5
MEMORY_LIMIT = 256 * 1024 * 1024


def _set_limits():
    if resource is None:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (EXECUTION_TIMEOUT, EXECUTION_TIMEOUT))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))


def _sanitize(text, workdir):
    if not text:
        return text
    return text.replace(workdir + "/", "").replace(workdir, "")


def execute(language_id, code, user_input=""):
    lang = get_language(language_id)
    if not lang:
        return {"success": False, "output": f"Unsupported language: {language_id}", "error": ""}

    workdir = tempfile.mkdtemp(prefix="oc_")

    try:
        if language_id == "java":
            src_filename = f"{lang['main_class']}.java"
        else:
            src_filename = f"main.{lang['extension']}"

        src_path = os.path.join(workdir, src_filename)
        exe_path = os.path.join(workdir, "main.out")

        with open(src_path, "w") as f:
            f.write(code)

        if lang["needs_compile"]:
            compile_cmd = [
                arg.format(src=src_path, exe=exe_path, workdir=workdir)
                for arg in lang["compile_cmd"]
            ]
            try:
                result = subprocess.run(
                    compile_cmd,
                    capture_output=True,
                    text=True,
                    timeout=COMPILE_TIMEOUT,
                    cwd=workdir,
                )
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "output": f"Compilation timed out after {COMPILE_TIMEOUT}s",
                    "error": "",
                }

            if result.returncode != 0:
                return {
                    "success": False,
                    "output": _sanitize(result.stderr, workdir),
                    "error": "",
                }

        run_cmd = [
            arg.format(src=src_path, exe=exe_path, workdir=workdir)
            for arg in lang["run_cmd"]
        ]

        try:
            result = subprocess.run(
                run_cmd,
                input=user_input,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT,
                cwd=workdir,
                preexec_fn=_set_limits if resource else None,
            )

            return {
                "success": True,
                "output": _sanitize(result.stdout, workdir),
                "error": _sanitize(result.stderr, workdir),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": f"Execution timed out after {EXECUTION_TIMEOUT}s",
                "error": "",
            }
        except Exception as e:
            return {
                "success": False,
                "output": f"Runtime error: {str(e)}",
                "error": "",
            }

    finally:
        shutil.rmtree(workdir, ignore_errors=True)
