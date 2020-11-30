import os
import sys
import streamlit as st


from cool.lexer import tokenizer
from cool.parser import CoolParser
from cool.cmp import evaluate_reverse_parse
from cool.semantic import TypeCollectorVisitor, TypeBuilderVisitor, TypeCheckerVisitor, TypeInfererVisitor

st.title("INFERENCIA DE TIPOS PARA COOL")
st.subheader("Ingrese el código cool a compilar")

text = st.text_area("Código Cool","")

if st.button("Compilar"):    
    #LEXER
    tokens = tokenizer(text)

    #PARSING
    parse, operations = CoolParser(tokens)
    if not operations:
        st.error("PARSING ERROR")
    
    #CONSTRUYENDO AST
    ast = evaluate_reverse_parse(parse, operations, tokens)

    st.subheader("Primera pasada sobre el AST para crear un contexto y recolectar todos los tipos definidos")
    errors = []
    a = TypeCollectorVisitor(errors)
    a.visit(ast)
    context = a.context
    strcontext=str(context).split('\n')
    
    st.success("Contexto")    
    st.write(str(context))

    st.subheader("Segunda pasada sobre el AST para agregar al contexto la construcción de métodos y atributos")
    a = TypeBuilderVisitor(context, errors)    
    a.visit(ast)
    st.success("Contexto")
    st.write(str(context))

    st.subheader("Tercera pasada sobre el AST para verificar la consistencia de los tipos en todos los nodos del AST")
    a = TypeCheckerVisitor(context, errors)
    scope = a.visit(ast)    
    st.error("Errores detectados en las primeras tres pasadas")
    for error in errors:
        st.write(error)

    st.subheader("Cuarta pasada sobre el AST para inferir los tipos segun el contexto y el scope")
    inferences = []
    a = TypeInfererVisitor(context, errors, inferences)
    #while a.visit(ast, scope): pass
    a.visit(ast,scope)
    st.warning("Tipos inferidos")
    for inference in inferences:
        st.write(inference)
  
    