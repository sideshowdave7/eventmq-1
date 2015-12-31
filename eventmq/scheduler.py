# This file is part of eventmq.
#
# eventmq is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# eventmq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with eventmq.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod:`scheduler` -- Scheduler
=============================
Handles cron and other scheduled tasks
"""
import json
import logging
import time

from croniter import croniter
from six import next

from .sender import Sender
from .poller import Poller, POLLIN
from .utils.classes import EMQPService, HeartbeatMixin
from .utils.timeutils import seconds_until, timestamp, monotonic
from .client.messages import send_request


logger = logging.getLogger(__name__)


class Scheduler(HeartbeatMixin, EMQPService):
    """
    Keeper of time, master of schedules
    """
    SERVICE_TYPE = 'scheduler'

    def __init__(self, *args, **kwargs):
        logger.info('Initializing Scheduler...')
        super(Scheduler, self).__init__(*args, **kwargs)
        self.outgoing = Sender()

        # contains 4-item lists representing cron jobs
        # IDX     Description
        # 0 = the next ts this job should be executed in
        # 1 = the function to be executed
        # 2 = the croniter iterator for this job
        # 3 = the queue to execute the job in
        self.cron_jobs = []

        # contains 4-item lists representing jobs based on an interval
        # IDX     Descriptions
        # 0 = the next (monotonic) ts that this job should be executed in
        # 1 = the function to be executed
        # 2 = the interval iter for this job
        # 3 = the queue to execute the job in
        self.interval_jobs = []

        self.poller = Poller()

        self.load_jobs()

        self._setup()

    def load_jobs(self):
        """
        Loads the jobs that need to be scheduled
        """
        raw_jobs = (
            # ('* * * * *', 'eventmq.scheduler.test_job'),
        )
        ts = int(timestamp())
        for job in raw_jobs:
            # Create the croniter iterator
            c = croniter(job[0])
            path = '.'.join(job[1].split('.')[:-1])
            callable_ = job.split('.')[-1]

            msg = ['run', {
                'path': path,
                'callable': callable_
            }]

            # Get the next time this job should be run
            c_next = next(c)
            if ts >= c_next:
                # If the next execution time has passed move the iterator to
                # the following time
                c_next = next(c)
            self.cron_jobs.append([c_next, msg, c, None])

    def _start_event_loop(self):
        """
        Starts the actual event loop. Usually called by :meth:`Scheduler.start`
        """
        while True:
            ts_now = int(timestamp())
            m_now = monotonic()
            events = self.poller.poll()

            if events.get(self.outgoing) == POLLIN:
                msg = self.outgoing.recv_multipart()
                self.process_message(msg)

            # TODO: distribute me!
            for i in range(0, len(self.cron_jobs)):
                # If the time is now, or passed
                if self.cron_jobs[i][0] <= ts_now:
                    msg = self.cron_jobs[i][1]
                    queue = self.cron_jobs[i][3]

                    # Run the msg
                    logger.debug("Time is: %s; Schedule is: %s - Running %s"
                                 % (ts_now, self.cron_jobs[i][0], msg))

                    self.send_request(self.outgoing, msg, queue=queue)

                    # Update the next time to run
                    self.cron_jobs[i][0] = next(self.cron_jobs[i][2])
                    logger.debug("Next execution will be in %ss" %
                                 seconds_until(self.cron_jobs[i][0]))

            for i in range(0, len(self.interval_jobs)):
                if self.interval_jobs[i][0] <= m_now:
                    msg = self.interval_jobs[i][1]
                    queue = self.interval_jobs[i][3]

                    logger.debug("Time is: %s; Schedule is: %s - Running %s"
                                 % (ts_now, self.interval_jobs[i][0], msg))

                    self.send_request(msg, queue=queue)
                    self.interval_jobs[i][0] = next(self.interval_jobs[i][2])

    def send_request(self, jobmsg, queue=None):
        jobmsg = json.loads(jobmsg)
        send_request(self.outgoing, jobmsg, queue=queue)

    def on_schedule(self, msgid, message):
        """
        """
        from .utils.timeutils import IntervalIter

        logger.info("Received new SCHEDULE request: {}".format(message))

        queue = message[0]
        interval = int(message[1])
        inter_iter = IntervalIter(monotonic(), interval)

        self.interval_jobs.append([
            next(inter_iter),
            message[2],
            inter_iter,
            queue
        ])

        self.send_request(message[2], queue=queue)


def test_job():
    print "hello!"
    print "hello!"
    time.sleep(4)
