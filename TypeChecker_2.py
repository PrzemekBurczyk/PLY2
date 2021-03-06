#!/usr/bin/python

from SymbolTable import VariableSymbol
from SymbolTable import SymbolTable
from SymbolTable import Symbol

ttype = {}
arithm_ops = [ '+', '-', '*', '/', '%' ]
bit_ops = [ '|', '&', '^', '<<', '>>' ]
log_ops = [ '&&', '||' ]
comp_ops = [ '==', '!=', '>', '<', '<=', '>=' ]
ass_op = ['=']

for op in arithm_ops + bit_ops + log_ops + ass_op + comp_ops:
    ttype[op] = {}
    for type_ in ['int', 'float', 'string']:
        ttype[op][type_] = {}

for arithm_op in arithm_ops:
    ttype[arithm_op]['int']['int'] = 'int'
    ttype[arithm_op]['int']['float'] = 'float'
    ttype[arithm_op]['float']['int'] = 'float'
    ttype[arithm_op]['float']['float'] = 'float'
ttype['+']['string']['string'] = 'string'
ttype['*']['string']['int'] = 'string'
ttype['=']['float']['int'] = 'float'
ttype['=']['float']['float'] = 'float'
ttype['=']['int']['int'] = 'int'
ttype['=']['string']['string'] = 'string'

for op in bit_ops + log_ops:
    ttype[op]['int']['int'] = 'int'

for comp_op in comp_ops:
    ttype[comp_op]['int']['int'] = 'int'
    ttype[comp_op]['int']['float'] = 'int'
    ttype[comp_op]['float']['int'] = 'int'
    ttype[comp_op]['float']['float'] = 'int'
    ttype[comp_op]['string']['string'] = 'int'

class IncompatibleTypesError(Exception):
    pass

class DuplicatedSymbolError(Exception):
    pass

class SymbolNotDeclaredError(Exception):
    pass

class TypeChecker(object):

    def dispatch(self, node, *args):
        self.node = node
        className = node.__class__.__name__
        meth = getattr(self, 'visit_' + className)
        return meth(node, *args)
    
    def findVariable(self, tab, variable):
        #print "finding:", variable, "in:", tab.symbols
        if tab.symbols.has_key(variable):
            return tab.get(variable)
        elif tab.symbol.name == variable:
            #print "Returning function symbol of type", tab.symbol.type
            return tab.symbol
        elif tab.getParentScope() != None:
            return self.findVariable(tab.getParentScope(), variable)
        else:
            return None

    def visit_Program(self, node):
        tab = SymbolTable(None, "program", None)
        self.dispatch(node.declarations, tab)
        self.dispatch(node.fundefs, tab)
        self.dispatch(node.instructions, tab)

    def visit_Declarations(self, node, tab):
        for declaration in node.declarations:
            self.dispatch(declaration, tab)
            
    def visit_Declaration(self, node, tab):
        self.dispatch(node.inits, tab, node.type)

    def visit_Inits(self, node, tab, type):
        for init in node.inits:
            self.dispatch(init, tab, type)

    def visit_Init(self, node, tab, type):
        #print "init:", node.id, type
        errorOccured = False
        for symbol in tab.symbols:
            if symbol == node.id:
                print "Duplicated usage of symbol {0} in line {1}".format(node.id, node.line)
                errorOccured = True
                #raise DuplicatedSymbolError
        if not errorOccured:        
            tab.put(node.id, VariableSymbol(node.id, type, node.expression))
        

    def visit_Instructions(self, node, tab):
        for instruction in node.instructions:
            self.dispatch(instruction, tab)
 
    def visit_Instruction(self, node, tab):
        pass

    def visit_Print(self, node, tab):
        self.dispatch(node.expression, tab)

    def visit_Labeled(self, node, tab):
        self.dispatch(node.instruction, tab)
        
    def visit_Assignment(self, node, tab):
        variable = self.findVariable(tab, node.id)
        if variable == None:
            print "Symbol {0} in line {1} not defined before".format(node.id, node.line)
        else:
            valueType = self.dispatch(node.expression, tab)
            if not ttype["="][variable.type].has_key(valueType):
                #print variable.name, variable.type
                print "Value of type {0} cannot be assigned to symbol {1} of type {2} (line {3})".format(valueType, node.id, variable.type, node.line)
            else:
                return ttype["="][variable.type][valueType]
        
    def visit_Choice(self, node, tab):
        self.dispatch(node._if, tab)
        self.dispatch(node._if, tab)

    def visit_If(self, node, tab):
        self.dispatch(node.cond, tab)
        self.dispatch(node.statement, tab)

    def visit_Else(self, node, tab):
        self.dispatch(node.statement, tab)

    def visit_While(self, node, tab):
        self.dispatch(node.cond, tab)
        self.dispatch(node.statement, tab)

    def visit_RepeatUntil(self, node, tab):
        self.dispatch(node.cond, tab)
        self.dispatch(node.statement, tab)

    def visit_Return(self, node, tab):
        self.dispatch(node.expression, tab)

    def visit_Continue(self, node, tab):
        pass

    def visit_Break(self, node, tab):
        pass

    def visit_Compound(self, node, tab, *args):
        if len(args) > 0 and args[0] is True:
            self.dispatch(node.declarations, tab)
            self.dispatch(node.instructions, tab)
        else:
            new_tab = SymbolTable(tab, None, None)
            self.dispatch(node.declarations, new_tab)
            self.dispatch(node.instructions, new_tab)
        
    def visit_Condition(self, node, tab):
        pass
    
    def visit_Expression(self, node, tab):
        pass

    def visit_Const(self, node, tab):
        value = node.value
        if (value[0] == '"' or value[0] == "'") and (value[len(value) - 1] == '"' or value[len(value) - 1] == "'"):
            return 'string'
        try:
            int(value)
            return 'int'
        except ValueError:
            try:
                float(value)
                return 'float'
            except ValueError:
                print "Value's {0} type is not recognized".format(value)

    def visit_Id(self, node, tab):
        #print "ID:", node.id
        variable = self.findVariable(tab, node.id)
        if variable == None:
            print "Symbol {0} in line {1} not declared before".format(node.id, node.line)
        else:
            return variable.type

    def visit_BinExpr(self, node, tab):
        try:
            type1 = self.dispatch(node.expr1, tab)
            type2 = self.dispatch(node.expr2, tab)
            op = node.operator;
            #print type1, type2, op
            return ttype[op][type1][type2]
        except KeyError:
            print "Incompatible types in line", node.line
            #raise IncompatibleTypesError
        except IncompatibleTypesError:
            pass
            #raise IncompatibleTypesError

    def visit_ExpressionInParentheses(self, node, tab):
        expression = node.expression
        return self.dispatch(expression, tab)
    
    def visit_IdWithParentheses(self, node, tab):
        variable = self.findVariable(tab, node.id)
        if variable == None:
            print "Symbol {0} in line {1} not declared before".format(node.id, node.line)
        else:
            self.dispatch(node.expression_list, tab)
            return variable.type

    def visit_ExpressionList(self, node, tab):
        for expression in node.expressions:
            self.dispatch(expression, tab)

    def visit_FunctionDefinitions(self, node, tab):
        for fundef in node.fundefs:
            self.dispatch(fundef, tab)

    def visit_FunctionDefinition(self, node, tab):
        new_tab = SymbolTable(tab, node.id, node.type)
        self.dispatch(node.arglist, new_tab)
        self.dispatch(node.compound_instr, new_tab, True)
    
    def visit_ArgumentList(self, node, tab):
        for arg in node.arg_list:
            self.dispatch(arg, tab)

    def visit_Argument(self, node, tab):
        #print "fun args:", node.id, node.type
        errorOccured = False
        for symbol in tab.symbols:
            if symbol == node.id:
                print "Duplicated usage of symbol {0} in line {1}".format(node.id, node.line)
                errorOccured = True
                #raise DuplicatedSymbolError
        if not errorOccured:
            tab.put(node.id, VariableSymbol(node.id, node.type, None))
            return node.type
    
