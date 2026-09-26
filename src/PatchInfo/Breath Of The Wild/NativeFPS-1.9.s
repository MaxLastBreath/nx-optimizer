// BOTW 1.9.0 / CD57B23FA4BBAD65803D9788C01821EE
// Assembled at the addresses documented in tools/build_botw_native_payload.py.
// The text cave is unused page padding after .text (0x015A1C64).
// State at 0x01DB21E0 occupies alignment padding before .bss (0x01DB2200).
// No original game code is included in this payload.

// @block limiter 0x015A1C80
// Replaces the last GetSystemTick call in the framework's frame loop.
// Returns the current tick in x0, preserving the original call's ABI.
stp x29, x30, [sp, #-0x30]!
mov x29, sp
stp x19, x20, [sp, #0x10]
stp x21, x22, [sp, #0x20]
adrp x19, 0x01DB2000
add x19, x19, #0x1E0
bl 0x015A0C20
mov x20, x0
ldr w8, 0x015A1FC0
udiv x21, x20, x8
bl 0x0159FF00
ldr x22, [x19]
cbz x22, first_frame
wait_frame:
sub x9, x0, x22
cmp x9, x21
b.hs frame_ready
sub x0, x21, x9
bl 0x015A0A10
bl 0x015A0A00
bl 0x0159FF00
b wait_frame
first_frame:
mov x9, x21
frame_ready:
str x0, [x19]
ucvtf s0, x9
ucvtf s1, x20
fdiv s0, s0, s1
fmov s1, #30.0
fmul s0, s0, s1
// Avoid a huge simulation jump after a loading stall or suspension.
fmov s1, #3.0
fmin s0, s0, s1
str s0, [x19, #8]
ldp x21, x22, [sp, #0x20]
ldp x19, x20, [sp, #0x10]
ldp x29, x30, [sp], #0x30
ret

// @block fov 0x015A1E80
// Replaces the CameraMgr store to the active world camera's FOV at +0x74.
// Scale the freshly calculated angle, preserving relative aim/cutscene zoom.
// s16 is dead at this callsite; NZCV and x8 are preserved.
ldr s16, 0x015A1FC4
fmul s0, s0, s16
ldr s16, 0x015A1FD0
fmin s0, s0, s16
ldr s16, 0x015A1FCC
fmax s0, s0, s16
str s0, [x8, #0x74]
ret

// @block far_clip 0x015A1EC0
// Replaces only the active world camera's far plane store.
ldr s0, 0x015A1FC8
str s0, [x8, #0x70]
ret

// @block delta 0x015A1E00
// Inline call replacing FCMP s1,s0 in VFRMgr::update. Native code still
// handles pause/category multipliers and publishes the resulting time values.
adrp x16, 0x01DB2000
ldr s1, [x16, #0x1E8]
fcmp s1, #0.0
b.gt have_delta
ldr w16, 0x015A1FC0
ucvtf s1, w16
fmov s16, #30.0
fdiv s1, s16, s1
have_delta:
str s1, [x19, #0x30]
fcmp s1, s0
ret
