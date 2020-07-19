
" TODO:
" [x] Return value of last expression in block (switchable)
"
" [x] Allow restarting the interpreter with a command
"
" [ ] Clear cell command + clear all command
"
" [ ] Run all cells up & including current one command
"
" [ ] Colorize marker lines (switchable)
"     #== color whole line with a grayish color to create a visual delimiter
"     #=| light green?
"     #=! red
"
" [ ] [MAYBE] Set up some key bindings (switchable)
"
" [ ] [MAYBE] Return value of arbitrary variables using
"     smth like "#== a foo_bar baz", allow all expressions that do not contain
"     space
"
" [ ] [MAYBE] Extend the above to allow multiple lines of expression spec like
"     #=? a + b
"     #=? f(3, 4) + [0, 1]
"     #=? Foo().bar("foo bar bang")

if exists("g:loaded_pythonblocks")
	finish
endif

if !exists('g:pythonblocks#marker_prefix')
	let g:pythonblocks#marker_prefix = '#='
endif

if !exists('g:pythonblocks#marker_cell')
	let g:pythonblocks#marker_cell = '='
endif

if !exists('g:pythonblocks#marker_value')
	let g:pythonblocks#marker_value = '>'
endif

if !exists('g:pythonblocks#marker_stdout')
	let g:pythonblocks#marker_stdout = '|'
endif

if !exists('g:pythonblocks#marker_stderr')
	let g:pythonblocks#marker_stderr = '!'
endif

let s:bin_dir = expand('<sfile>:h:h') . '/bin/'

function! s:init_python() abort
	let l:init_lines = [
				\ 'import sys',
				\ 'import os',
				\ 'sys.path.append("' . s:bin_dir . '")',
				\ 'if "pythonblocks" in sys.modules:',
				\ '  del sys.modules["pythonblocks"]',
				\ 'import pythonblocks' ]

	exec 'py3 exec('''.escape(join(l:init_lines, '\n'), "'").''')'
endfunction

function! pythonblocks#TidySelection()
	" Tidy the visual selection of all pythonblocks output lines except for
	" cell markers
	" Update the visual selection to account for deleted lines.
	exec "normal! gv"
	let l:start = line("'<")
	let l:end = line("'>")
	let l:lines = line("$")
	exec l:start . "," . l:end . ' g/^\V' . g:pythonblocks#marker_prefix . '\(' . g:pythonblocks#marker_cell . '\)\@!/d'
	let l:deleted = l:lines - line("$")
	call setpos("'>", [0, l:end - l:deleted, 1, 0])
endfunction

function! pythonblocks#RunFile(...) abort
	" Execute the given file with python.
	" If no file is given, use the filename of the current buffer.
	let l:filename = a:0 ? a:000[-1] : expand("%:p")
	exec "py3file " . l:filename
endfunction

function! pythonblocks#RunCell()
	" Set up a visual selection spanning the current cell as defined by
	" sourrounding cell markers.
	" Tidy the selection from pythonblocks outputs and run it in python,
	" potentially creating new output.
	exec 'normal! ?^' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\|\%^' . "\n"
	exec 'normal! V/^' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\|\%$' . "\n"
	exec "normal! \<esc>gv"

	call pythonblocks#TidySelection()
	exec "normal! gv"

	'<,'> py3 pythonblocks.run_range()
	exec "normal! \<esc>"
endfunction

call s:init_python()

command! -buffer -nargs=* -complete=file PythonblocksRunFile call pythonblocks#RunFile(<f-args>)
command! PythonblocksRunCell call pythonblocks#RunCell()
command! PythonblocksTidySelection call pythonblocks#TidySelection()
command! PythonblocksRestart py3 pythonblocks.restart()


