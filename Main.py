import sys
import random
import sys
import music21
from mido import MidiFile, MidiTrack, Message, MetaMessage

MINOR   = [+0, +3, +7]
MAJOR   = [+0, +4, +7]
DIM     = [+0, +3, +6]
SUS2    = [+0, +2, +7]
SUS4    = [+0, +5, +7]

ACCORDS = [MINOR, MAJOR, DIM, SUS2, SUS4]

SCALE_POINT = 0.25

CORRELATION_POINT = 0.25

SCALE_TYPE = {
    'minor': [2, 3, 5, 7, 8, 10, 12],  # 2 1 2 2 1 2 2
    'major': [2, 4, 5, 7, 9, 11, 12]  # 2 2 1 2 2 2 1
}

class Generation:
    def __init__(self, individual_numbers, chord_numbers):
        self.individauls = []
        for i in range(individual_numbers):
            self.individauls.append(Individaul(chord_numbers))

    def trim(self, goal):
        sorted_individauls = []
        for individaul in self.individauls:
            sorted_individauls.append((get_fitness(individaul), individaul))
        sorted_individauls.sort(key=lambda a: a[0], reverse=True)
        
        sorted_individauls = sorted_individauls[:int(goal)]
        # while(len(sorted_individauls) > goal):
        #     sorted_individauls.pop()

        self.individauls = [pair[1] for pair in sorted_individauls]

    def evolve(self, goal):
        self.trim(goal * 0.25)
        for i in range(goal - len(self.individauls)):
            parent1 = Individaul()
            parent2 = Individaul()
            # parent3 = Individaul()
            parent1.chords = (random.choice(self.individauls)).chords[:]
            parent2.chords = (random.choice(self.individauls)).chords[:]
            parent1.crossover(parent2)
            parent3 = random.choice(self.individauls)
            parent3.mutate()
        
        
class Individaul:

    def __init__(self, *args):
        self.chords = []
        if(len(args) == 1):
            chord_num = args[0]
            for i in range(chord_num):
                self.chords.append(Chord(random.randint(0, 12 - 1), random.choice(ACCORDS)))

    def crossover(self, other):
        sz = len(self.chords)
        chunk = random.randint(1, sz - 1)
        start_indx = random.randint(0, sz - 1 - chunk)
        first = self.chords
        second = other.chords
        first[start_indx:start_indx + chunk], second[start_indx:start_indx + chunk] = second[
                                                                                        start_indx:start_indx + chunk], first[
                                                                                                                        start_indx:start_indx + chunk]
        self.chords = first
        other.chords = second


    def mutate(self):
        chord_index = random.randint(0, len(self.chords) - 1)
        self.chords[chord_index] = Chord(random.randint(0, 12 - 1), random.choice(ACCORDS))


class Chord:
    def __init__(self, *args):
        if isinstance(args[0], list):
            self.notes = args[0]
        if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], list):
            self.notes = [(args[0] + x) % 12 for x in args[1]]

    def __eq__(self, other):
        if len(self.notes) != len(other.notes): return False
        for i in range(len(self.notes)):
            if self.notes[i] != other.notes[i]: return False
        return True


def in_scale(chord: Chord):
    score = float(0)
    for note in chord.notes:
        if note in SCALE:
            score += SCALE_POINT
    return score

def in_timestamp(chord: Chord, list):
    score = float(0)
    for note in chord.notes:
        if note in list:
            score += CORRELATION_POINT
    return score


def get_fitness(individaul: Individaul):
    fitness = float(0)

    for i in range(len(timestamp)):
        fitness += in_scale(individaul.chords[i])
        fitness += in_timestamp(individaul.chords[i], timestamp[i])
    return fitness


def add_chord(chord: Chord):
    if len(mid.tracks) <= 2: mid.tracks.append(MidiTrack())
    for note in chord.notes:
        mid.tracks[2].append(Message('note_on', note=note, velocity=VELOCITY, time=0, channel=0))
    mid.tracks[2].append(Message('note_off', note=chord.notes[0], velocity=VELOCITY, time=DURATION, channel=0))
    for note in chord.notes:
        if(note != chord.notes[0]):
            mid.tracks[2].append(Message('note_off', note=note, velocity=VELOCITY, time=0, channel=0))


def genereate_accompaniment(number_of_generations, individual_numbers, output_file):
    input_length = 0
    for i in range(len(mid.tracks[1])):
        if not mid.tracks[1][i].is_meta:
            input_length += mid.tracks[1][i].time

    chords_number = (input_length) // DURATION
    if input_length % DURATION > 0: chords_number += 1

    generation = Generation(individual_numbers, chords_number)
    for i in range(number_of_generations):
        generation.evolve(individual_numbers)
    generation.trim(1)

    last_gen = generation.individauls[0]

    for i in range(len(last_gen.chords)):
        print(last_gen.chords[i].notes, timestamp[i])

    for chord in generation.individauls[0].chords:
        chord_in_octave = Chord([12 * OCTAVE + note for note in chord.notes])
        add_chord(chord_in_octave)
    mid.save(filename=output_file)


if len(sys.argv) <= 1:
    print("Pass an input file as an argument for the .py")
input_file = sys.argv[1]
mid = MidiFile(input_file, clip=True)

NUM = input_file[5]

key = music21.converter.parse(input_file).analyze('key')

DURATION = (mid.ticks_per_beat * 2)
VELOCITY = 30

KEY_NOTE = key.pitches[0].midi
OCTAVE = key.pitches[0].octave - 1
REWARD = 0.5

SCALE = [(KEY_NOTE + i) % 12 for i in SCALE_TYPE[key.mode]]

cur_time = 0
timestamp = []
interval = []
cnt = 1
for msg in mid.tracks[1]:
    if msg.is_meta or msg.type == 'program_change': continue
    cur_time += msg.time
    if cur_time > (cnt + 1) * DURATION:
        cnt += 1
        timestamp.append(set(interval))
        interval = []
    interval.append(msg.note % 12)
timestamp.append(set(interval))

genereate_accompaniment(500, 300, "Output" + str(NUM) + "-" + str(key.tonic.name) + ".mid")

print(SCALE)
 
