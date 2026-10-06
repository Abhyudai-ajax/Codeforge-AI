from app.workers.sandbox import run_source

def test_exec():
    print("Testing Python local execution fallback...")
    res = run_source(
        language="python",
        source_code="import sys\nline = sys.stdin.read().strip()\nprint(f'Hello {line}!')",
        stdin="CodeForge",
        timeout_seconds=5.0,
        memory_mb=128
    )
    print("Stdout:", res.stdout.strip())
    print("Stderr:", res.stderr.strip())
    print("Exit code:", res.exit_code)
    assert res.exit_code == 0
    assert "Hello CodeForge!" in res.stdout
    print("Code execution test passed!")

if __name__ == "__main__":
    test_exec()
