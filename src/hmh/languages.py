"""Language registry: extensions, filenames and per-language comment rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Language:
    """How to recognise a language and how to count its lines."""

    name: str
    extensions: Tuple[str, ...] = ()
    filenames: Tuple[str, ...] = ()
    line_comments: Tuple[str, ...] = ()
    block_comments: Tuple[Tuple[str, str], ...] = ()
    strings: Tuple[str, ...] = ()
    multiline_strings: Tuple[str, ...] = ()


def _lang(
    name: str,
    extensions: Sequence[str] = (),
    filenames: Sequence[str] = (),
    line: Sequence[str] = (),
    block: Sequence[Tuple[str, str]] = (),
    strings: Sequence[str] = (),
    multiline: Sequence[str] = (),
) -> Language:
    return Language(
        name=name,
        extensions=tuple(extensions),
        filenames=tuple(filenames),
        line_comments=tuple(line),
        block_comments=tuple(block),
        strings=tuple(strings),
        multiline_strings=tuple(multiline),
    )


_C_BLOCK = (("/*", "*/"),)
_QUOTE_STRINGS = ("'", '"')
_SLASH_LINE = ("//",)
_SLASH_BLOCK = _C_BLOCK
_HASH_LINE = ("#",)

_LANGUAGES: Tuple[Language, ...] = (
    # -- general purpose ------------------------------------------------
    _lang("Python", (".py", ".pyw", ".pyi"), ("setup.py", "conftest.py"),
          line=_HASH_LINE, strings=_QUOTE_STRINGS, multiline=("'''", '"""')),
    _lang("JavaScript", (".js", ".mjs", ".cjs", ".jsx"), line=_SLASH_LINE,
          block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("TypeScript", (".ts", ".tsx", ".mts", ".cts"), line=_SLASH_LINE,
          block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Java", (".java",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("C", (".c", ".h"), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("C++", (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".inl"),
          line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("C#", (".cs",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Go", (".go",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Rust", (".rs",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Ruby", (".rb", ".rake", ".gemspec"), ("Rakefile", "Gemfile", "Berksfile"),
          line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("PHP", (".php", ".phtml", ".php3", ".php4", ".php5"),
          line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Swift", (".swift",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Kotlin", (".kt", ".kts"), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Scala", (".scala", ".sc"), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Objective-C", (".m", ".mm"), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Dart", (".dart",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Groovy", (".groovy", ".gradle"), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Perl", (".pl", ".pm", ".pod"), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("Lua", (".lua",), line=("--",), block=(("--[[", "]]"),), strings=_QUOTE_STRINGS),
    _lang("R", (".r",), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("Julia", (".jl",), line=_HASH_LINE, block=(("=", "="),), strings=_QUOTE_STRINGS),
    _lang("Haskell", (".hs", ".lhs"), line=("--",), block=(("{-", "-}"),)),
    _lang("Elixir", (".ex", ".exs"), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("Erlang", (".erl", ".hrl"), line=("%",), strings=_QUOTE_STRINGS),
    _lang("Clojure", (".clj", ".cljs", ".cljc", ".edn"), line=(";",), strings=_QUOTE_STRINGS),
    _lang("Zig", (".zig",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Nim", (".nim",), line=("#",), strings=_QUOTE_STRINGS),
    _lang("Crystal", (".cr",), line=("#",), strings=_QUOTE_STRINGS),
    _lang("Solidity", (".sol",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Fortran", (".f", ".f90", ".f95", ".f03", ".for"), line=("!",), strings=_QUOTE_STRINGS),
    _lang("Ada", (".adb", ".ads"), line=("--",), strings=_QUOTE_STRINGS),
    _lang("VHDL", (".vhd", ".vhdl"), line=("--",), strings=_QUOTE_STRINGS),
    _lang("Verilog", (".v", ".sv", ".vhd"), line=("//",), block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("Prolog", (".pro", ".plg"), line=("%",), strings=_QUOTE_STRINGS),
    _lang("Lisp", (".lisp", ".el", ".scm", ".lsp", ".cl"), line=(";",), strings=_QUOTE_STRINGS),
    _lang("Assembly", (".asm", ".s", ".S"), line=(";", "//", ";", "#"),
          block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),

    # -- shell / scripting ---------------------------------------------
    _lang("Shell", (".sh", ".bash", ".zsh", ".ksh", ".fish", ".command"),
          line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("PowerShell", (".ps1", ".psm1", ".psd1"), line=_HASH_LINE,
          block=(("<#", "#>"),), strings=_QUOTE_STRINGS),
    _lang("Batch", (".bat", ".cmd"), line=("REM ", "rem ", "::")),
    _lang("Vim script", (".vim",), line=('"',)),

    # -- web / data / config -------------------------------------------
    _lang("HTML", (".html", ".htm", ".xhtml"), block=(("<!--", "-->"),)),
    _lang("XML", (".xml", ".xsd", ".xsl", ".xslt", ".plist", ".svg", ".resx"),
          block=(("<!--", "-->"),)),
    _lang("CSS", (".css",), block=_SLASH_BLOCK),
    _lang("SCSS", (".scss",), line=_SLASH_LINE, block=_SLASH_BLOCK),
    _lang("Sass", (".sass",), line=_SLASH_LINE),
    _lang("Less", (".less",), line=_SLASH_LINE, block=_SLASH_BLOCK),
    _lang("Vue", (".vue",), line=_SLASH_LINE, block=_SLASH_BLOCK + (("<!--", "-->"),),
          strings=_QUOTE_STRINGS),
    _lang("Svelte", (".svelte",), line=_SLASH_LINE, block=_SLASH_BLOCK + (("<!--", "-->"),),
          strings=_QUOTE_STRINGS),
    _lang("JSON", (".json", ".json5", ".jsonc"), strings=_QUOTE_STRINGS),
    _lang("YAML", (".yaml", ".yml"), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("TOML", (".toml",), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("INI", (".ini", ".cfg", ".conf", ".properties", ".env"),
          line=("#", ";"), strings=_QUOTE_STRINGS),
    _lang("Markdown", (".md", ".markdown", ".mdx", ".mdown"), strings=()),
    _lang("reStructuredText", (".rst",)),
    _lang("CSV", (".csv", ".tsv")),
    _lang("Text", (".txt", ".log")),
    _lang("TeX", (".tex", ".sty", ".cls", ".bib", ".bbl"), line=("%",), strings=_QUOTE_STRINGS),
    _lang("Dockerfile", (".dockerfile",), ("Dockerfile", "Containerfile"), line=_HASH_LINE),
    _lang("Makefile", (".mk",), ("Makefile", "makefile", "GNUmakefile", "Makefile.am"),
          line=_HASH_LINE),
    _lang("CMake", (".cmake",), ("CMakeLists.txt",), line=_HASH_LINE),
    _lang("Terraform", (".tf", ".tfvars", ".hcl"), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("Starlark", (".bzl",), ("BUILD", "WORKSPACE", "BUILD.bazel", "WORKSPACE.bazel"),
          line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("Nix", (".nix",), line=_HASH_LINE, strings=_QUOTE_STRINGS),
    _lang("Protocol Buffers", (".proto",), line=_SLASH_LINE, block=_SLASH_BLOCK, strings=_QUOTE_STRINGS),
    _lang("GraphQL", (".graphql", ".gql"), line=("#",), block=(('"""', '"""'),),
          strings=_QUOTE_STRINGS),
    _lang("Smarty/Template", (".tpl", ".twig", ".jinja", ".jinja2", ".j2", ".liquid"),
          line=("#", "//"), strings=_QUOTE_STRINGS),
)

LANGUAGES: Dict[str, Language] = {language.name: language for language in _LANGUAGES}

EXTENSION_MAP: Dict[str, str] = {}
FILENAME_MAP: Dict[str, str] = {}
for _language in _LANGUAGES:
    for _ext in _language.extensions:
        EXTENSION_MAP.setdefault(_ext.lower(), _language.name)
    for _name in _language.filenames:
        FILENAME_MAP.setdefault(_name.lower(), _language.name)

#: Extensions whose content is never line-counted, only weighed.
BINARY_EXTENSIONS = frozenset(
    # images
    ".png .jpg .jpeg .gif .bmp .ico .icns .webp .tiff .tif .psd .raw".split()
    # fonts
    + ".woff .woff2 .ttf .otf .eot".split()
    # archives / binaries
    + ".zip .gz .tgz .bz2 .xz .rar .7z .jar .war .ear .class .o .a .obj .lib .dll .so .dylib .exe .bin .out .pyc .pyo .pyd .wasm".split()
    # media
    + ".mp3 .mp4 .avi .mov .mkv .webm .wav .flac .ogg .m4a .wmv .mpeg .mpg".split()
    # documents / data blobs
    + ".pdf .doc .docx .xls .xlsx .ppt .pptx .odt .db .sqlite .sqlite3 .parquet .pickle .pkl .npy .npz .pt .h5 .hdf5".split()
)

#: Directories skipped unless explicitly requested.
DEFAULT_EXCLUDE_DIRS = frozenset(
    (".git .hg .svn .bzr .idea .vscode .cursor .DS_Store __pycache__ "
     "node_modules jspm_packages bower_components .mypy_cache .pytest_cache "
     ".ruff_cache .tox .nox .venv venv env .env .next .nuxt .output .svelte-kit "
     "target .gradle .m2 vendor coverage .coverage htmlcov .eggs .cache "
     "site-packages .terraform .serverless .parcel-cache .turbo .pnpm-store").split()
)

#: Directory names matched anywhere, e.g. ``something.egg-info``.
DEFAULT_EXCLUDE_PATTERNS = ("*.egg-info", "*.dist-info", "*.node_modules")

_SHEBANG_LANGUAGES = {
    "python": "Python",
    "python3": "Python",
    "node": "JavaScript",
    "nodejs": "JavaScript",
    "deno": "TypeScript",
    "bun": "JavaScript",
    "bash": "Shell",
    "sh": "Shell",
    "zsh": "Shell",
    "dash": "Shell",
    "ruby": "Ruby",
    "perl": "Perl",
    "lua": "Lua",
    "php": "PHP",
    "rscript": "R",
    "julia": "Julia",
    "pwsh": "PowerShell",
    "powershell": "PowerShell",
}


def detect(path: str, head: bytes = b"") -> Optional[str]:
    """Return the language of ``path``.

    ``head`` is the first chunk of the file, used for ``#!`` shebangs when the
    name alone is ambiguous. Returns ``None`` when unknown.
    """
    name = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if name in FILENAME_MAP:
        return FILENAME_MAP[name]

    lowered = path.replace("\\", "/").lower()
    dot = lowered.rfind(".")
    if dot != -1:
        language = EXTENSION_MAP.get(lowered[dot:])
        if language:
            return language

    if head.startswith(b"#!"):
        first_line = head.split(b"\n", 1)[0].decode("utf-8", "ignore")
        tokens = first_line.replace("=", " ").split()
        if tokens:
            interpreter = tokens[0].rsplit("/", 1)[-1].lower()
            if interpreter in ("env", "env.exe"):
                for token in tokens[1:]:
                    found = _SHEBANG_LANGUAGES.get(token.rsplit("/", 1)[-1].lower())
                    if found:
                        return found
                return None
            return _SHEBANG_LANGUAGES.get(interpreter)
    return None


def _starts_with(line: str, index: int, tokens: Tuple[str, ...]) -> Optional[str]:
    for token in tokens:
        if line.startswith(token, index):
            return token
    return None


@dataclass
class _ScanState:
    """Cross-line state for block comments and multi-line strings."""

    block_end: Optional[str] = None
    string_end: Optional[str] = None


def _classify_line(line: str, language: Language, state: _ScanState) -> str:
    """Classify one physical line as ``code``, ``comment`` or ``blank``."""
    index, length = 0, len(line)
    saw_code = saw_comment = False

    while index < length:
        # inside a string that opened on an earlier line
        if state.string_end is not None:
            found = line.find(state.string_end, index)
            saw_code = True
            if found < 0:
                return "code"
            index = found + len(state.string_end)
            state.string_end = None
            continue

        # inside a block comment that opened on an earlier line
        if state.block_end is not None:
            found = line.find(state.block_end, index)
            saw_comment = True
            if found < 0:
                return "comment"
            index = found + len(state.block_end)
            state.block_end = None
            continue

        # multi-line string opening (must be tested before single-quote rules)
        token = _starts_with(line, index, language.multiline_strings)
        if token is not None:
            found = line.find(token, index + len(token))
            saw_code = True
            if found < 0:
                state.string_end = token
                return "code"
            index = found + len(token)
            continue

        # block comment opening
        for start, end in language.block_comments:
            if line.startswith(start, index):
                found = line.find(end, index + len(start))
                saw_comment = True
                if found < 0:
                    state.block_end = end
                    return "comment"
                index = found + len(end)
                break
        else:
            # single-line string literal
            token = _starts_with(line, index, language.strings)
            if token is not None:
                cursor = index + len(token)
                while cursor < length:
                    if line[cursor] == "\\":
                        cursor += 2
                        continue
                    if line.startswith(token, cursor):
                        cursor += len(token)
                        break
                    cursor += 1
                saw_code = True
                index = cursor
                continue

            # line comment
            token = _starts_with(line, index, language.line_comments)
            if token is not None:
                saw_comment = True
                return "code" if saw_code else "comment"

            if not line[index].isspace():
                saw_code = True
            index += 1
            continue

        # reached only when the block-comment branch ran and closed inline
        continue

    if saw_code:
        return "code"
    if saw_comment:
        return "comment"
    return "blank"


def count_lines(text: str, language: Optional[str]) -> Tuple[int, int, int]:
    """Return ``(code, comment, blank)`` for ``text``.

    Languages without known comment syntax have every non-blank line counted as
    code, which matches how most counters behave.
    """
    spec = LANGUAGES.get(language or "")
    code = comment = blank = 0

    if spec is None:
        for line in text.splitlines():
            if line.strip():
                code += 1
            else:
                blank += 1
        return code, comment, blank

    state = _ScanState()
    for line in text.splitlines():
        if not line.strip():
            blank += 1
            continue
        verdict = _classify_line(line, spec, state)
        if verdict == "code":
            code += 1
        elif verdict == "comment":
            comment += 1
        else:
            blank += 1
    return code, comment, blank


def known_languages() -> Tuple[str, ...]:
    """Names of every language hmh recognises, alphabetically."""
    return tuple(sorted(LANGUAGES))
