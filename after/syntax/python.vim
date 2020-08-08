
let s:pref = strlen(g:pythonblocks#marker_prefix)

exec 'syn match pbCellPrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '/ nextgroup=pbCellText conceal cchar=#'
exec 'syn match pbCellText /.*$/ contained'

exec 'syn match pbStdoutPrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stdout . '/ nextgroup=pbStdoutText conceal cchar=>'
exec 'syn match pbStdoutText /.*$/ contained'

exec 'syn match pbStderrPrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stderr . '/ nextgroup=pbStderrText conceal cchar=>'
exec 'syn match pbStderrText /.*$/ contained'

exec 'syn match pbValuePrefix /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_value . '/ nextgroup=pbValueText conceal cchar=>'
exec 'syn match pbValueText /.*$/ contained'

hi link pbCellPrefix Folded
hi link pbCellText Folded

hi link pbStdoutPrefix Comment
hi pbStdoutText ctermfg=40

hi link pbStderrPrefix Comment
hi pbStderrText ctermfg=160

hi link pbValuePrefix Comment
hi pbValueText ctermfg=39
