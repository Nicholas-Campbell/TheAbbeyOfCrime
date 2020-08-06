; The Abbey of Crime - introduction text
;
; Byte 13 (&0D) indicates the end of a line
; Byte 26 (&1A) indicates the end of the text

; The introduction text in the English version needs to be moved to a higher
; address in memory to make room for additional characters in the font

org &7360

db " Having reached the",13
db "end of my poor sin-",13
db "ner's life, waiting to",13
db "be lost in the bottom-",13
db "less pit of silent and",13
db "deserted divinity, con-",13
db "fined now with my",13
db "heavy, ailing body in",13
db "this cell in the dear",13
db "monastery of Melk, I",13
db "prepare to leave on",13
db "this parchment my",13
db "testimony as to the",13
db "wondrous and terrible",13
db "events that I happened",13
db "to observe in my",13
db "youth.",13
db 13
db 13
db 13
db " May the Lord grant",13
db "me the grace to be",13
db "the transparent wit-",13
db "ness of the occur-",13
db "rences that took place",13
db "in the abbey whose",13
db "name it is only right",13
db "and pious now to omit,",13
db "toward the end of the",13
db "year of our Lord",13
db "1327, when my father",13
db "decided to place me",13
db "under the direction of",13
db "a learned Franciscan,",13
db "Brother William of",13
db "Baskerville, about to",13
db "undertake a mission",13
db "that would lead him",13
db "to famous cities and",13
db "ancient abbeys. Thus",13
db "I became William's",13
db "scribe and disciple at",13
db "the same time, nor",13
db "did I ever regret it,",13
db "because with him I",13
db "was witness to events",13
db "worthy of being handed",13
db "down, as I am now",13
db "doing, to those who",13
db "will come after us.",13
db " And so, after I had",13
db "come to know my",13
db "master day by day,",13
db "we reached the foot",13
db "of the hill on which",13
db "the abbey stood. And",13
db "it is time for my",13
db "story to approach it,",13
db "as we did then, and",13
db "may my hand remain",13
db "steady as I prepare",13
db "to tell what happened.",13
db 13
db 13
db 13
db 13
db 13
db 13
db 13
db 13
db "author: ",13
db "    Paco Menendez",13
db 13
db "graphics and cover:",13
db "    Juan Delcan",13
db 13
db "copyright:",13
db "    Opera Soft",13
db 26

; Unused bytes
db 0,0
