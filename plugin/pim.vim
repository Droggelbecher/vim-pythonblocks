
"if exists("g:loaded_pim")
	"finish
"endif

if !exists('g:pim#marker_prefix')
	let g:pim#marker_prefix = '#='
endif

if !exists('g:pim#marker_cell')
	let g:pim#marker_cell = '='
endif

if !exists('g:pim#marker_value')
	let g:pim#marker_value = '>'
endif

if !exists('g:pim#marker_stdout')
	let g:pim#marker_stdout = '|'
endif

if !exists('g:pim#marker_stderr')
	let g:pim#marker_stderr = '!'
endif

function! s:init_python() abort
	" TODO: Remove private paths
	let init_lines = [
				\ 'import sys',
				\ 'import os',
				\ 'sys.path.append("/home/henning/.vim/autoload")',
				\ 'if "pim" in sys.modules:',
				\ '  del sys.modules["pim"]',
				\ 'import pim' ]

	try
		exec 'py3 exec('''.escape(join(init_lines, '\n'), "'").''')'
	catch
		throw printf('[pim] failed to initialize python: %s.', v:exception)
	endtry
endfunction

function! pim#TidySelection()
	exec "normal! gv"
	let l:start = line("'<")
	let l:end = line("'>")
	let l:lines = line("$")
	exec l:start . "," . l:end . ' g/^\V' . g:pim#marker_prefix . '\(' . g:pim#marker_cell . '\)\@!/d'
	let l:deleted = l:lines - line("$")
	call setpos("'>", [0, l:end - l:deleted, 1, 0])
endfunction

function! pim#RunFile(...) abort
	let l:filename = a:0 ? a:000[-1] : expand("%:p")
	exec "py3file " . l:filename
endfunction

function! pim#RunCell()
	exec 'normal! ?^' . g:pim#marker_prefix . g:pim#marker_cell . '\|\%^' . "\n"
	exec 'normal! V/^' . g:pim#marker_prefix . g:pim#marker_cell . '\|\%$' . "\n"
	exec "normal! \<esc>gv"

	call pim#TidySelection()
	exec "normal! gv"

	'<,'> py3 pim.run_range()
	exec "normal! \<esc>"
endfunction

call s:init_python()

command! -buffer -nargs=* -complete=file PimRunFile call pim#RunFile(<f-args>)
command! PimRunCell call pim#RunCell()
command! PimTidy call pim#TidySelection()


