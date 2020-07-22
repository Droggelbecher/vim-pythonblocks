
" TODO:
" [x] Return value of last expression in block (switchable)
"
" [x] Allow restarting the interpreter with a command
"
" [x] Clear cell command + clear all command
"
" [x] Run all cells up & including current one command
"
" [x] Colorize marker lines (switchable)
"     #== color whole line with a grayish color to create a visual delimiter
"     #=| light green?
"     #=! red
"
" [x] On execution: trim all blank lines at end of cell, add blank lines
" around output
"
" [x] More correct marker handling at end-of-file. Either ensure theres always
"     a marker there or make a case-distinction based on line content in the
"     tidying
"
" [ ] Tidying/running leaves two blank lines at EOF, when it should be one
" like in all other cells
"
" [ ] Proper README, maybe a terminal recording to show off
"
" [x] Command to execute visual selection rather than current block
"
" [ ] Measure timing and report in marker (optionally)
"
" [ ] Optionally report last execution time in marker
"
" [ ] [MAYBE] Set up some key bindings (switchable)
"
" [ ] [MAYBE] Return value of arbitrary variables using
"     smth like "#== a foo_bar baz", allow all expressions that do not contain
"     space
"
" [ ] [MAYBE] Like the above but one expr per line like
"     #=? a + b
"     #=? f(3, 4) + [0, 1]
"     #=? Foo().bar("foo bar bang")
"
" [ ] [MAYBE] Use signs to allow highlighting complete lines for better visual
"     separation.
"     OR automagically change the cell makers to something long for this
"     purpose?
"

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

if !exists('g:pythonblocks#expand_marker')
	let g:pythonblocks#expand_marker = 1
endif

if !exists('g:pythonblocks#expand_marker_string')
	let g:pythonblocks#expand_marker_string = "                                                                                              ="
endif

if !exists('g:pythonblocks#visual_delay')
	let g:pythonblocks#visual_delay = '200m'
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

function! s:select_cell()
	exec "normal! \<esc>"
	if line(".") > 1
		exec 'normal! ?^' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\|\%^' . "\n"
	endif
	if line(".") < line("$")
		exec 'normal! V/^' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\|\%$' . "\n"
	endif
	exec "normal! \<esc>gv"
	redraw
	exec "sleep " . g:pythonblocks#visual_delay
endfunction

function! s:go_next_cell()
	let l:p = search('^' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\|\%$', 'W')
	call setpos('.', [0, l:p, 1, 0])
endfunction

function! s:select_next_cell()
	exec "normal! gv"
	exec "normal! \<esc>"
	call setpos('.', [0, line("'>") + 1, 1, 0])
	call s:select_cell()
endfunction

function! s:update_selection_end(end)
	let l:orig_pos = getpos('.')
	call setpos(".", [0, getpos("'>")[1], 1, 0])
	normal! g$
	let l:last_col = getpos(".")[2]
	call setpos("'>", [0, a:end, l:last_col, 0])
	call setpos(".", l:orig_pos)
endfunction

function! s:tidy_selection()
	" Tidy the visual selection of all pythonblocks output lines except for
	" cell markers
	" Update the visual selection to account for deleted lines.
	exec "normal! gv"
	let l:start = line("'<")
	let l:end = line("'>")

	" Delete all lines with marker_prefix not followed by marker_cell
	let l:lines = line("$")
	exec "silent! " . l:start . "," . l:end . ' g/^\V' . g:pythonblocks#marker_prefix . '\(' . g:pythonblocks#marker_cell . '\)\@!/d'
	let l:end -= l:lines - line("$")

	" Delete all blank lines at the end
	let l:lines = line("$")
	exec "silent! " . l:start . "," . l:end . ' g/\(^\s*$\n\)\+\%' . l:end . 'l/d'
	let l:end -= l:lines - line("$")

	" Expand cell markers

	let l:lines = line("$")
	if g:pythonblocks#expand_marker
		exec "silent! " . l:start . "," . l:end . ' s/^\V\(' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\)\s\*\$/\1 ' . g:pythonblocks#expand_marker_string . '/e'
	endif
	let l:end -= l:lines - line("$")

	call s:update_selection_end(l:end)
endfunction

function! s:run_selection()
	let l:begin = line("'<")
	let l:end = line("'>")
	exec "normal! \<esc>"
	let l:before = line("$")
	if l:end >= l:begin && l:end <= line("$")
		exec l:begin . ',' . l:end . 'py3 pythonblocks.run_range()'
	endif
	let l:end = l:end + line("$") - l:before
	call setpos("'>", [0, l:end, 1, 0])
endfunction


function! pythonblocks#AddCellMarker()
	call append(line("."), g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . ' ' . g:pythonblocks#expand_marker_string)
endfunction
	
function! pythonblocks#TidyCell()
	call s:select_cell()
	call s:tidy_selection()
	exec "normal \<esc>"
	if getline(".") =~ '^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\.\*'
		" This appending will be tracked by '> automatically!
		call append(line("'>") - 1, "")
	else
		call append(line("'>"), "")
	endif
endfunction

function! pythonblocks#TidyUntil(end)
	call setpos(".", [0, 0, 1, 0])
	let l:end = a:end
	let l:before = line("$")
	call pythonblocks#TidyCell()
	let l:end = l:end + line("$") - l:before
	while line(".") < l:end
		call s:go_next_cell()
		let l:before = line("$")
		call pythonblocks#TidyCell()
		" Move l:end to compensate for added/removed lines
		let l:end = l:end + line("$") - l:before
	endwhile
	exec "normal \<esc>"
endfunction


function! pythonblocks#RunCell()
	" Set up a visual selection spanning the current cell as defined by
	" sourrounding cell markers.
	" Tidy the selection from pythonblocks outputs and run it in python,
	" potentially creating new output.
	call pythonblocks#TidyCell()
	exec "normal! gv"

	call s:run_selection()
	exec "normal! gv"
	exec "normal! \<esc>"
	if getline(".") =~ '^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\.\*'
		" This appending will be tracked by '> automatically!
		call append(line("'>") - 1, "")
	else
		call append(line("'>"), "")
	endif
endfunction

function! pythonblocks#RunSelection()
	call s:tidy_selection()
	call s:run_selection()
endfunction

function! pythonblocks#RunUntil(end)
	call setpos(".", [0, 0, 1, 0])
	call pythonblocks#RunCell()
	let l:end = a:end
	while line(".") < l:end
		call s:go_next_cell()
		let l:before = line("$")
		call pythonblocks#RunCell()
		" Move l:end to compensate for removed lines
		let l:end = l:end + line("$") - l:before
	endwhile
	exec "normal \<esc>"
endfunction

function! pythonblocks#RunFile(...) abort
	" Execute the given file with python.
	" If no file is given, use the filename of the current buffer.
	let l:filename = a:0 ? a:000[-1] : expand("%:p")
	exec "py3file " . l:filename
endfunction



function! pythonblocks#test_cells()
	call setpos(".", [0, 0, 1, 0])
	call s:select_cell()
	while line(".") < line("$") - 1
		call s:go_next_cell()
		call s:select_cell()
	endwhile
	exec "normal \<esc>"
endfunction

function! pythonblocks#select_cell()
	call s:select_cell()
endfunction

call s:init_python()

command! PBRestart py3 pythonblocks.restart()

command! PBAddCellMarker call pythonblocks#AddCellMarker()

command! PBTidyCell call pythonblocks#TidyCell()
command! PBTidyUntil call pythonblocks#TidyUntil(line("."))
command! PBTidyAll call pythonblocks#TidyUntil(line("$") - 1)

command! PBRunCell call pythonblocks#RunCell()
command! PBRunUntil call pythonblocks#RunUntil(line("."))
command! PBRunAll call pythonblocks#RunUntil(line("$") - 1)

" We don't actually use the range here but rather query '< and '> directly,
" still its more convenient to use this way
command! -range PBRunSelection call pythonblocks#RunSelection()
command! -buffer -nargs=* -complete=file PythonblocksRunFile call pythonblocks#RunFile(<f-args>)

command! PBTest call pythonblocks#test_cells()
command! PBSel call pythonblocks#select_cell()

