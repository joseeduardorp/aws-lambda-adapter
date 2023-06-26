import argparse
import re
from pathlib import Path
from colorama import Fore, Style

from patterns import pattern
from templates import test_file
from templates import imports
from templates import constant
from templates import send_response_fn


def get_args():
    parser = argparse.ArgumentParser(
        description="Script para auxiliar na migração dos lambdas",
        usage="\n  python %(prog)s -f exemplo.js\n  python %(prog)s -d ./src -n index.js",
    )

    parser.add_argument(
        "-f",
        "--input-file",
        action="store",
        type=Path,
        dest="input_file",
        help="Específica o arquivo a ser adaptado",
    )

    parser.add_argument(
        "-d",
        "--directory",
        action="store",
        type=Path,
        dest="directory_path",
        help="Específica o diretório a ser escaneado a procura dos arquivos",
    )

    parser.add_argument(
        "-t",
        "--add-tests",
        action="store_true",
        dest="unit_test",
        help="Cria o arquivo 'index.test.ts' e adapta o lambda para o padrão com testes unitários",
    )

    parser.add_argument(
        "-n",
        "--file-name",
        action="store",
        default="index.js",
        type=str,
        dest="file_name",
        help="Usado com -d, específica o nome dos arquivos a serem procurados",
    )

    parser.add_argument(
        "-o",
        "--output-file",
        action="store",
        default="output.ts",
        type=str,
        dest="output_file",
        help="Específica o nome de saída dos arquivos",
    )

    parser.add_argument(
        "-r",
        "--replace",
        action="store_true",
        dest="replace",
        help="Força a substituição do arquivo 'index.ts'",
    )

    return parser.parse_args()


args = get_args()


def create_test_file(dir_path: Path):
    if not dir_path.is_dir():
        dir_path = dir_path.parent.resolve()

    abs_path = dir_path.resolve()
    function_name = abs_path.stem
    function_test_file = re.sub("nome_da_funcao", function_name, test_file.TEST)

    output_path = abs_path.joinpath("__tests__")

    if not output_path.exists():
        output_path.mkdir()

    output_path = abs_path.joinpath("__tests__", "index.test.ts")

    if output_path.exists():
        print(
            f"{Fore.YELLOW}[!] {function_name} - arquivo 'index.test.ts' já existe{Style.RESET_ALL}"
        )
        return

    file = open(output_path, mode="w", encoding="utf-8")
    file.write(function_test_file)
    file.close()


def addIgnoreClause(output_path: Path):
    function_file = open(output_path, "rt")
    lines = function_file.readlines()
    function_file.close()

    content = ""

    for current_line in lines:
        if re.search("__non_webpack_require__", current_line):
            current_line = "// @ts-ignore\n" + current_line

        content = content + current_line

    file = open(output_path, mode="w", encoding="utf-8")
    file.write(content)
    file.close()


def handleImports(content: str):
    new_content = content

    if args.unit_test:
        # adiciona as constantes 'isTest' e '_require'
        new_content = f"{constant.IS_TEST}\n{constant.REQUIRE}\n" + new_content

        # substitui a importação do 'aws-sdk'
        new_content = re.sub(
            pattern.AWS_REQUIRE,
            imports.TEST_AWS_REQUIRE,
            new_content,
            flags=re.IGNORECASE,
        )

        # substitui a instância 'db' do dynamoDB
        new_content = re.sub(
            pattern.DB_INSTANCE,
            imports.TEST_DB_REQUIRE,
            new_content,
            flags=re.IGNORECASE,
        )

        # substitui a importação da layer 'AuthorizerUtils'
        new_content = re.sub(
            pattern.AUTHORIZER_REQUIRE,
            imports.TEST_AUTHORIZER_REQUIRE,
            new_content,
            flags=re.IGNORECASE,
        )

        # verifica se o sentry está sendo usado
        sentry_instance = re.search(pattern.SENTRY_INSTANCE, new_content, re.IGNORECASE)

        if sentry_instance != None:
            # substitui a importação do 'Sentry'
            new_content = re.sub(
                pattern.SENTRY_REQUIRE,
                imports.TEST_SENTRY_REQUIRE,
                new_content,
                flags=re.IGNORECASE,
            )

            instance = sentry_instance.group()

            # coloca a instância do Sentry dentro de um bloco condicional
            conditional_sentry = re.sub(
                "sentry_instance", instance, constant.SENTRY, flags=re.IGNORECASE
            )
            new_content = re.sub(
                pattern.SENTRY_INSTANCE,
                conditional_sentry,
                new_content,
                flags=re.IGNORECASE,
            )

    # verifica se a layer é usada
    # se sim, adiciona a importação
    has_authorizer = re.findall("AuthorizerUtils", new_content, re.IGNORECASE)
    if len(has_authorizer) > 0:
        new_content = f"{imports.AUTHORIZER_INTERFACE_IMPORT}\n" + new_content

    # procura pelos métodos do banco de dados
    # se encontrar, faz as importações necessárias
    dbActions = re.findall(pattern.DB_ACTIONS, new_content, re.IGNORECASE)
    if len(dbActions) > 0:
        dbActions = list(dict.fromkeys(dbActions))

        formatedParams = []
        for action in dbActions:
            formatedParams.append(f"{action.capitalize()}ParamsI")

        paramsImport = ", ".join(formatedParams)
        paramsImport = re.sub("typed_db_actions", paramsImport, imports.DB_ACTIONS_IMPORTS)

        new_content = f"{paramsImport}\n" + new_content

    # adiciona importação do "aws-lambda"
    new_content = imports.LAMBDA_IMPORT + new_content

    if not args.unit_test:
        # substitui o "require" por "__non_webpack_require__"
        new_content = re.sub("require\(", "__non_webpack_require__(", new_content)

    return new_content


def handleDbParams(content: str):
    # procurando pelo nome e declaração dos parâmetros
    dbParams = re.findall(pattern.PARAMS, content, re.IGNORECASE)
    paramNames = re.findall(pattern.PARAM_NAMES, content, re.IGNORECASE)

    param_types = {}
    for param in paramNames:
        try:
            # procurando em que métodos do banco os parâmetros são usados
            db_method_pattern = f"db\s*\.\s*(\w+)\({param}\)"
            method = re.search(db_method_pattern, content, re.IGNORECASE)

            _type = f"{method.group(1).capitalize()}ParamsI"
            param_types.update({param: _type})
        except:
            raise Exception("Houve um erro ao tentar criar as importações dos métodos do banco")

    new_content = content
    for param in dbParams:
        try:
            declaration = param[0]
            typing = param_types[param[1]]

            sub = f"{declaration}: {typing}"
            new_content = re.sub(declaration, sub, new_content)
        except:
            raise Exception("Houve um erro ao tipar os parâmetros de métodos do banco")

    return new_content


def addReturnSendResponseFn(matchobj: re.Match):
    ret = matchobj.group()
    status_code = re.search(pattern.RET_STATUS_CODE, ret, re.IGNORECASE)
    body = re.search(pattern.RET_BODY, ret, re.IGNORECASE)

    new_return = re.sub(
        "status_code",
        status_code.group(1),
        send_response_fn.CALL_FN,
        flags=re.IGNORECASE,
    )
    new_return = re.sub("body", body.group(1), new_return, flags=re.IGNORECASE)

    return new_return


def transpile(file_path: Path):
    if not file_path.is_file():
        print("Específique um arquivo")
        return

    # pega o conteúdo do arquivo
    abs_path = file_path.resolve()
    function_file = open(abs_path, "rt")
    content = function_file.read()
    function_file.close()

    # ...
    new_content = handleImports(content)
    new_content = handleDbParams(new_content)

    # remove o parenteses final do método 'wrapHandler'
    new_content = re.sub(pattern.LAMBDA_FUNCTION, "\g<1>", new_content)

    has_sentry = re.search("sentry", new_content, re.IGNORECASE)

    if args.unit_test:
        # substitui o handler da função pelo handler para testes
        new_content = re.sub(pattern.HANDLER, constant.HANDLER_TEST, new_content)

        if has_sentry:
            new_content = new_content + constant.HANDLER_SENTRY_EXPORT
        else:
            new_content = new_content + constant.HANDLER_EXPORT
    elif has_sentry:
        # substitui o handler da função pelo handler com sentry tipado
        new_content = re.sub(pattern.HANDLER, constant.HANDLER_SENTRY_TYPED, new_content)
    else:
        # substitui o handler da função pelo handler tipado
        new_content = re.sub(pattern.HANDLER, constant.HANDLER_TYPED, new_content)

    # adiciona a tipagem 'any' à variável 'event'
    new_content = re.sub(pattern.EVENT_VAR, "\g<1>: any\g<2>", new_content, re.IGNORECASE)

    # adiciona tipagem às instâncias da layer "AuthorizerUtil"
    authDeclarations = re.findall(pattern.AUTHORIZER_INSTANCE, content, re.IGNORECASE)
    for declaration in authDeclarations:
        sub = declaration + ": AuthorizerUtilsI"
        new_content = re.sub(declaration, sub, new_content)

    # adiciona a função sendResponse
    response_headers = re.search(pattern.DEFAULT_RESPONSE_HEADERS, new_content, re.IGNORECASE)
    function_added = f"{response_headers.group()}\n\n{send_response_fn.SEND_RESPONSE_FN}"
    new_content = re.sub(
        pattern.DEFAULT_RESPONSE_HEADERS,
        function_added,
        new_content,
        flags=re.IGNORECASE,
    )

    # substitui todos os 'returns' pela chamada da função sendResponse
    new_content = re.sub(pattern.RETURN, addReturnSendResponseFn, new_content, flags=re.IGNORECASE)

    output_path = abs_path.with_name(args.output_file)

    if output_path.exists() and not args.replace:
        raise Exception(
            f"Arquivo '{args.output_file}' já existe. Use -r para forçar a substituição do arquivo."
        )

    file = open(output_path, mode="w", encoding="utf-8")
    file.write(new_content)
    file.close()

    if not args.unit_test:
        # adiciona "// @ts-ignore" às importações com "__non_webpack_require__"
        addIgnoreClause(output_path)


def main():
    # -f e -d
    if args.input_file != None and args.directory_path != None:
        print("Não é possível usar esses argumentos juntos")
        exit()

    # -f
    if args.input_file != None:
        file_path = Path(args.input_file)
        function_name = list(file_path.parts)[-2]

        try:
            transpile(file_path)
            print(f"{Fore.GREEN}[+] {function_name} - adaptado com sucesso{Style.RESET_ALL}")

            # -t
            if args.unit_test:
                create_test_file(file_path)
        except Exception as e:
            print(f"{Fore.RED}[-] {function_name} - {e} {Style.RESET_ALL}")

    # -d
    if args.directory_path != None:
        directory_path = Path(args.directory_path).resolve()
        file_paths = list(directory_path.rglob(args.file_name))

        def remove_node_modules_paths(path):
            if re.search("node_modules", str(path)):
                return False
            else:
                return True

        paths = list(filter(remove_node_modules_paths, file_paths))

        for path in paths:
            function_name = list(path.parts)[-2]

            try:
                transpile(path)
                print(f"{Fore.GREEN}[+] {function_name} - adaptado com sucesso{Style.RESET_ALL}")

                # -t
                if args.unit_test:
                    create_test_file(path)
            except Exception as e:
                print(f"{Fore.RED}[-] {function_name} - {e}{Style.RESET_ALL}")


main()
