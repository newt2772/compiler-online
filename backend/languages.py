LANGUAGES = {
    "cpp": {
        "name": "C++",
        "extension": "cpp",
        "compile_cmd": ["g++", "{src}", "-o", "{exe}"],
        "run_cmd": ["{exe}"],
        "needs_compile": True,
        "starter_code": '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n    cout << "You entered: " << n << endl;\n    return 0;\n}'
    },
    "c": {
        "name": "C",
        "extension": "c",
        "compile_cmd": ["gcc", "{src}", "-o", "{exe}"],
        "run_cmd": ["{exe}"],
        "needs_compile": True,
        "starter_code": '#include <stdio.h>\n\nint main() {\n    int n;\n    scanf("%d", &n);\n    printf("You entered: %d\\n", n);\n    return 0;\n}'
    },
    "python": {
        "name": "Python 3",
        "extension": "py",
        "compile_cmd": None,
        "run_cmd": ["python3", "{src}"],
        "needs_compile": False,
        "starter_code": 'n = int(input())\nprint(f"You entered: {n}")'
    },
    "java": {
        "name": "Java",
        "extension": "java",
        "compile_cmd": ["javac", "{src}"],
        "run_cmd": ["java", "-cp", "{workdir}", "Main"],
        "needs_compile": True,
        "main_class": "Main",
        "starter_code": 'import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        int n = sc.nextInt();\n        System.out.println("You entered: " + n);\n    }\n}'
    },
    "javascript": {
        "name": "JavaScript (Node.js)",
        "extension": "js",
        "compile_cmd": None,
        "run_cmd": ["node", "{src}"],
        "needs_compile": False,
        "starter_code": "process.stdin.resume();\nlet data = '';\nprocess.stdin.on('data', (chunk) => data += chunk);\nprocess.stdin.on('end', () => {\n    const n = parseInt(data.trim());\n    console.log(`You entered: ${n}`);\n});"
    }
}


def get_language(lang_id):
    return LANGUAGES.get(lang_id)


def list_languages():
    return [
        {"id": lang_id, "name": cfg["name"], "starter_code": cfg["starter_code"]}
        for lang_id, cfg in LANGUAGES.items()
    ]
