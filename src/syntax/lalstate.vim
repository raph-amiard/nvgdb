" Vim syntax file
" Language: lal state

if exists("b:current_syntax")
  finish
endif

syn match  LalstateRunningProp "\v(Running )@<=.+"
syn match  LalstateSloc "\v(from )@<=.+"
syn match  LalstateCurrentExpr "\v(Currently evaluating )@<=.+"

syn region LalstatevarValRegion start="\v^\w+ \(" end="\n"
syn region LalstateExprEvalRegion start="\v^\<" end="\n"

syn match LalstateVarName "\v^\w+" contained containedin=LalstatevarValRegion
syn match LalstateGenCodeVarName "\v\(\w+\)" contained containedin=LalstatevarValRegion,LalstateExprEvalRegion
syn match LalstateValue "\v( \= )@<=.+" contained containedin=LalstatevarValRegion
syn match LalstateExpr "\v^\<(.{-})?\>" contained containedin=LalstateExprEvalRegion
syn match LalstateExprEvalValue "\v( \-\> )@<=.+" contained containedin=LalstateExprEvalRegion

hi def link LalstateRunningProp     Statement
hi def link LalstateSloc            Type
hi def link LalstateCurrentExpr     Identifier
hi def link LalstateExpr            Identifier
hi def link LalstateVarName         Function
hi def link LalstateGenCodeVarName  Constant
hi def link LalstateValue           String
hi def link LalstateExprEvalValue   String
