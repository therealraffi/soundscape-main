analysis = [[6, 826], [5, 826], [5, 826], [5, 826]]
angles = [[70.47311638118093, 0], [188.7402959508126, 1], [27.883596528122773, 2], [236.99031274902035, 3]]

#the blind sport degrees
ignore = 90
#number of motor pairs/group
nummotors = 8
#represents each motor group
motors = [0] * nummotors
inc = (360 - ignore) / (nummotors - 1)

# if len(angles) != 0:
    # print(angles)
print(angles)
for c in range(len(angles) - 1, -1, -1):
    i = angles[c]
    if (180 - ignore)/2 + inc/2 < i[0] < (180 + ignore)/2 - inc/2:
        del angles[c]
print(angles)
print()

possible = [(int((180 + ignore)/2 + i * inc)) % 360 for i in range(nummotors - 1)]
possible.insert(0, (180 - ignore)/2)
possible.sort()
print(possible)
print(analysis)
for angle, channel in angles:
    ind = 0
    for c, k in enumerate(possible):
        if k - inc/2 <= angle <= k + inc/2:
            ind = c
            if motors[ind] != 0:
                if ind == nummotors - 1:
                    if motors[0] == 0:
                        ind = 0
                        break
                    if motors[4] == 0:
                        ind = 4
                        break
                else:
                    if motors[ind + 1] == 0:
                        ind += 1
                        break
                    if motors[ind - 1] == 0:
                        ind -= 1
                        break
            else:
                break
    #amplitude should be between 0 and 100 since arduino multiplies pwm by 2.55
    motors[ind] = [max(analysis[channel][0] * 90/100, 0), analysis[channel][1]] if analysis[channel][0] > 0 else 0

# print(analysis)
print()
print(motors)
# print("\n\n")
# amp = max(analysis[0][0], analysis[1][0], analysis[2][0], analysis[3][0])

# print("%3s %6s \t %3s %6s \t %3s %6s \t %3s %6s" % (analysis[0][0], analysis[0][1], analysis[1][0], analysis[1][1], analysis[2][0], analysis[2][1], analysis[3][0], analysis[3][1]), amp * "|")

amps = [0] * 16

for c, i in enumerate(motors):
    if i == 0:
        amps[2 * c] = 0
        continue
    #low freqs
    elif i[1] < 640:
        amps[2 * c] = i[0]
    #high freqs
    else:
        amps[2 * c + 1] = i[0]

print(amps)

out = "<%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s>" % (amps[1], amps[2], amps[3], amps[4], amps[5], amps[6], amps[7], amps[8], amps[9], amps[10], amps[11], amps[12], amps[13], amps[14], amps[15], amps[0])
# teensy.write(out.encode())