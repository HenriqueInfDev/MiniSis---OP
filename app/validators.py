# app/validators.py
from validate_docbr import CPF, CNPJ

def validate_cpf_cnpj(doc):
    """
    Valida um número de CPF ou CNPJ.
    Retorna (True, 'cpf'/'cnpj') se válido, ou (False, None) se inválido.
    """
    cpf = CPF()
    cnpj = CNPJ()

    if cpf.validate(doc):
        return True, 'cpf'
    elif cnpj.validate(doc):
        return True, 'cnpj'
    else:
        return False, None
