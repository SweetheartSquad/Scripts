import sys
import os
import json

if len(sys.argv) >= 2:
    for file_idx in range(1, len(sys.argv)):
        anim_file_path = sys.argv[file_idx]
        if not os.path.isfile(anim_file_path):
            print "Invalid animation file"
            exit()
        with open(anim_file_path, 'r+') as anim_file:
            file_str = anim_file.read()
            anim_json = json.loads(file_str)

            left_arm = [0, 0]
            right_arm = [0, 0]
            left_leg = [0, 0]
            right_leg = [0, 0]
            body = [0, 0]

            for idx in range(1, len(anim_json)):
                left_arm[0] += anim_json[idx]['leftArm'][0]
                left_arm[1] += anim_json[idx]['leftArm'][1]
                right_arm[0] += anim_json[idx]['rightArm'][0]
                right_arm[1] += anim_json[idx]['rightArm'][1]
                left_leg[0] += anim_json[idx]['leftLeg'][0]
                left_leg[1] += anim_json[idx]['leftLeg'][1]
                right_leg[0] += anim_json[idx]['rightLeg'][0]
                right_leg[1] += anim_json[idx]['rightLeg'][1]
                body[0] += anim_json[idx]['body'][0]
                body[1] += anim_json[idx]['body'][1]

            left_arm[0] *= -1
            left_arm[1] *= -1
            right_arm[0] *= -1
            right_arm[1] *= -1
            left_leg[0] *= -1
            left_leg[1] *= -1
            right_leg[0] *= -1
            right_leg[1] *= -1
            body[0] *= -1
            body[1] *= -1

            end_frame = {
                'interpolation': 'LINEAR',
                'time': 0.3,
                'leftArm': left_arm,
                'rightArm': right_arm,
                'leftLeg': left_leg,
                'rightLeg': right_leg,
                'body': body
            }

            anim_json.append(end_frame)
            anim_file.seek(0)
            anim_file.write(json.dumps(anim_json, indent=4, sort_keys=True))
            anim_file.truncate()
else:
    print "Expected Animation File"
