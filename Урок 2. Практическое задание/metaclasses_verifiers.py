import dis


# Метакласс, выполняющий базовую проверку классов клиентской программы
class ClientVerifier(type):
    def __init__(self, clsname, bases, clsdct):
        # clsname - экземпляр метакласса - Client
        # bases - кортеж базовых классов - ()
        # clsdct - словарь атрибутов и методов экземпляра метакласса
        methods = []  # Список методов дочернего класса
        attrs = []  # Список атрибутов методов дочернего класса
        for clsmethod in clsdct:
            try:
                gen_meth_code = dis.get_instructions(clsdct[clsmethod])
            except TypeError:  # Если не функция
                pass
            else:  # Если функция, получаем используемые методы
                for m in gen_meth_code:
                    # m - Instruction(opname='LOAD_GLOBAL', opcode=116, arg=9, argval='send_message',
                    # argrepr='send_message', offset=308, starts_line=201, is_jump_target=False)
                    # opname - имя для операции
                    if m.opname == 'LOAD_GLOBAL':
                        if m.argval not in methods:
                            # Наполняем список методов класса:
                            methods.append(m.argval)
                    elif m.opname == 'LOAD_ATTR':
                        if m.argval not in attrs:
                            # Наполняем список атрибутов методов класса:
                            attrs.append(m.argval)
        # В случае наличия вызовов accept, listen, socket - исключение:
        for m in ('accept', 'listen'):
            if m in methods:
                raise TypeError('Попытка использования методов сервера!')
        # get_message или send_message из globals - корректное использование сокетов
        if not ('get_message' in methods or 'send_message' in methods):
            raise TypeError('Функции, работающие с сокетами не используются!')
        # В случае если сокет не инициализировался для работы по TCP (аргументы SOCK_STREAM, AF_INET), исключение:
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета!')
        # Вызывает конструктор родительского класса:
        super().__init__(clsname, bases, clsdct)


# Метакласс, выполняющий базовую проверку классов серверной программы
class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdct):
        # clsname - экземпляр метакласса - Server
        # bases - кортеж базовых классов - ()
        # clsdct - словарь атрибутов и методов экземпляра метакласса
        methods = []  # Список методов дочернего класса
        attrs = []  # Список атрибутов методов дочернего класса
        for clsmethod in clsdct:
            try:
                gen_meth_code = dis.get_instructions(clsdct[clsmethod])
            except TypeError:
                pass
            else:
                for m in gen_meth_code:
                    # m - Instruction(opname='LOAD_GLOBAL', opcode=116, arg=9, argval='send_message',
                    # argrepr='send_message', offset=308, starts_line=201, is_jump_target=False)
                    # opname - имя для операции
                    if m.opname == 'LOAD_GLOBAL':
                        if m.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(m.argval)
                    elif m.opname == 'LOAD_ATTR':
                        if m.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(m.argval)
        # В случае обнаружения клиентского метода connect, исключение:
        if 'connect' in methods:
            raise TypeError('Метод "Сonnect" недопустим в серверной пррограмме')
        # В случае если сокет не инициализировался для работы по TCP (аргументы SOCK_STREAM, AF_INET), исключение:
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета!')
        # Вызывает конструктор родительского класса:
        super().__init__(clsname, bases, clsdct)
