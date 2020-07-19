
syn clear pbCellMarker
syn clear pbStdout
syn clear pbStderr
syn clear pbValue

exec 'syn match pbCellMarker /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_cell . '\.\*/'

exec 'syn match pbStdout /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stdout . '/'
exec 'syn match pbStderr /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_stderr . '/'
exec 'syn match pbValue /^\V' . g:pythonblocks#marker_prefix . g:pythonblocks#marker_value . '/'


hi clear pbCellMarker
hi clear pbStdout
hi clear pbStderr
hi clear pbValue

hi pbCellMarker ctermbg=240 ctermfg=235
hi pbStdout ctermbg=34 ctermfg=78
hi pbStderr ctermbg=124 ctermfg=160
hi pbValue ctermbg=31 ctermfg=235
