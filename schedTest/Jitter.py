# Suspension as release jitter, given by Eq 2.
# Input: Task set
# Output: Schedulability of task set
import itertools
import math


class DLMiss(Exception):
    """Exception raised when DL miss detected."""

    def __init__(self):
        super().__init__("DL miss detected")


def SuspJit(tasks, k=0):
    for idx in range(len(tasks)):
        wcrt = SuspJit_WCRT(tasks[idx], tasks[:idx])
        if wcrt > tasks[idx]["deadline"]:  # deadline miss
            return False
        else:
            tasks[idx]["wcrt_jit"] = wcrt  # set wcrt
            continue
    return True


# Compute the response time bound using Eq 2.
# Input: Task, higher priority tasks
# Output: Worst-case response time of task
def SuspJit_WCRT(task, HPTasks):
    t = task["execution"] + task["sslength"]
    while True:
        # Compute lhs of Eq 2.
        wcrt = task["execution"] + task["sslength"]
        for itask in HPTasks:
            wcrt += (
                math.ceil(
                    (t + itask["wcrt_jit"] - itask["execution"]) / itask["period"]
                )
                * itask["execution"]
            )
        if wcrt > task["deadline"] or wcrt <= t:  # deadline miss  # Eq 2 holds
            break
        t = wcrt  # increase t for next iteration
    return wcrt


def _wcrt_rec(task, HPTasks, jitters, time):
    assert len(HPTasks) == len(jitters)
    result = 0
    result += task["execution"] + task["sslength"]
    for itask, ijitter in zip(HPTasks, jitters):
        result += math.ceil((time + ijitter) / itask["period"]) * itask["execution"]
    return result


def wcrt(task, HPTasks, HPWcrts, k=0):
    rt = 0
    zipped = list(zip(HPTasks, HPWcrts))
    for ordered in itertools.permutations(zipped):
        if len(ordered) == 0:
            ord_HPTasks = []
            ord_HPWcrt = []
        else:
            ord_HPTasks, ord_HPWcrt = zip(*ordered)

        # Construct jitters
        jitters = []
        Rem_sum = 0
        for tsk, wcrt in zip(ord_HPTasks, ord_HPWcrt):
            Rem_sum += tsk["execution"]
            jitters.append(max(wcrt - Rem_sum, 0))  # TODO: Do I need this maximum?

        # calculate wcrt
        time_prev = -1
        time = 0
        while time > time_prev:
            time_prev = time
            time = _wcrt_rec(task, ord_HPTasks, jitters, time_prev)

            if time > task["deadline"]:
                raise DLMiss()  # DL miss detected

        rt = max(rt, time)

    return rt


def sched_test(taskset):
    # Speed up for testing # TODO: remove
    if SuspJit(taskset):
        return True

    rts = []
    try:
        for idx in range(len(taskset)):
            rt = wcrt(taskset[idx], taskset[:idx], rts)
            rts.append(rt)
    except DLMiss:
        return False

    return True


if __name__ == "__main__":
    from tgPath import taskGeneration_p as generatetss

    ts = generatetss(3, 0.5, 0.01, 0.1)

    print(sched_test(ts))
