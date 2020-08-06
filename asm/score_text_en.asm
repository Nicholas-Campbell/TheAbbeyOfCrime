; The Abbey of Crime - text used when displaying the player's final score
; upon failure to complete the game

org &4305

; Do not alter the length of the string below (15 bytes)!
db "YOU HAVE SOLVED",255

; The game copies the final score to the first three bytes of the string below,
; so do not alter them!
ld hl,&300e
ld (&2d97),hl
call &4fee
db "  0   PER CENT",255

ld hl,&400c
ld (&2d97),hl
call &4fee
db "OF THE INVESTIGATION",255

ld hl,&8006
ld (&2d97),hl
call &4fee
db "PRESS SPACE TO START AGAIN",255
