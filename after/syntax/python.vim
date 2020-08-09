
let s:pref = strlen(g:pythonblocks#marker_prefix)

exec 'syn match pbCell /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\.\*\$/ contains=pbCellPrefix'
exec 'syn match pbCellPrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '/ conceal cchar=# contained'

exec 'syn match pbStdout /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stdout . '\.\*\$/ contains=pbStdoutPrefix'
exec 'syn match pbStdoutPrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stdout . '/ conceal cchar=> contained'

exec 'syn match pbStderr /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stderr . '\.\*\$/ contains=pbStderrPrefix'
exec 'syn match pbStderrPrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stderr . '/ conceal cchar=> contained'

exec 'syn match pbValue /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_value . '\.\*\$/ contains=pbValuePrefix'
exec 'syn match pbValuePrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_value . '/ conceal cchar=> contained'

hi link pbCellPrefix Folded
hi link pbCell Folded

hi link pbStdoutPrefix Comment
hi pbStdout ctermfg=40

hi link pbStderrPrefix Comment
hi pbStderr ctermfg=160

hi pbValue ctermfg=39
hi link pbValuePrefix Comment
