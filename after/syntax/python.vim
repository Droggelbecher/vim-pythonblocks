
let s:pref = strlen(g:pythonblocks#marker_prefix)

exec 'syn match pbCellMarker /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\.\*/'

exec 'syn match pbStdout /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stdout . '\.\*/'
exec 'syn match pbStdoutText /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stdout . ' \zs\.\*/ containedin=pbStdout'

exec 'syn match pbStderr /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stderr . '\.\*/'
exec 'syn match pbStderrText /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stderr . ' \zs\.\*/ containedin=pbStderr'

exec 'syn match pbValue /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_value . '\.\*/'
exec 'syn match pbValueText /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_value . ' \zs\.\*/ containedin=pbValue'

hi link pbCellMarker Folded

hi link pbStdout Comment
hi pbStdoutText ctermfg=40

hi link pbStderr Comment
hi pbStderrText ctermfg=160

hi link pbValue Comment
hi pbValueText ctermfg=39
