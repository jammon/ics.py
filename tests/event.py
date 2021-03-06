import unittest
from datetime import datetime, timedelta
from ics.event import Event
from ics.icalendar import Calendar
from ics.utils import parse_date_or_datetime, tzutc
from .fixture import cal12, calendar_with_duration_and_end, cal15, cal16

CRLF = "\r\n"


class TestEvent(unittest.TestCase):

    def test_event(self):
        e = Event(begin=0, end=20)
        self.assertEqual(e.begin, datetime.fromtimestamp(0, tz=tzutc))
        self.assertEqual(e.end, datetime.fromtimestamp(20, tz=tzutc))
        self.assertTrue(e.has_end())
        self.assertFalse(e.all_day)

        f = Event(begin=10, end=30)
        self.assertTrue(e < f)
        self.assertTrue(e <= f)
        self.assertTrue(f > e)
        self.assertTrue(f >= e)

    def test_or(self):
        g = Event(begin=0, end=10) | Event(begin=10, end=20)
        self.assertEqual(g, (None, None))

        def timestamp(dt):
            return (dt - datetime.fromtimestamp(0, tz=tzutc)).total_seconds()

        g = Event(begin=0, end=20) | Event(begin=10, end=30)
        self.assertEqual(tuple(map(timestamp, g)), (10, 20))

        g = Event(begin=0, end=20) | Event(begin=5, end=15)
        self.assertEqual(tuple(map(timestamp, g)), (5, 15))

        g = Event() | Event()
        self.assertEqual(g, (None, None))

    def test_event_with_duration(self):
        c = Calendar(cal12)
        e = c.events[0]
        self.assertTrue(e._has_duration())
        self.assertEqual(e.duration, timedelta(1, 3600))
        self.assertEqual(e.end - e.begin, timedelta(1, 3600))

    def test_not_duration_and_end(self):
        c = Calendar(calendar_with_duration_and_end)
        with self.assertRaises(ValueError):
            c.validate()

    def test_duration_output(self):
        e = Event(begin=0, duration=timedelta(1, 23))
        lines = str(e).splitlines()
        self.assertIn('DTSTART:19700101T000000Z', lines)
        self.assertIn('DURATION:P1DT23S', lines)

    def test_make_all_day(self):
        e = Event(begin=0, end=20)
        begin = e.begin
        e.make_all_day()
        self.assertEqual(e.begin, begin.date())
        self.assertEqual(e.end, begin.date())
        self.assertEqual(e.duration, timedelta(1))

    def test_init_duration_end(self):
        with self.assertRaises(ValueError):
            Event(name="plop", begin=0, end=10, duration=1)

    def test_end_before_begin(self):
        e = Event(begin="2013/10/10")
        with self.assertRaises(ValueError):
            e.end = "1999/10/10"

    def test_begin_after_end(self):
        e = Event(end="19991010")
        with self.assertRaises(ValueError):
            e.begin = "2013/10/10"

    def test_plain_repr(self):
        self.assertEqual(repr(Event()), "<Event>")

    def test_all_day_repr(self):
        e = Event(name='plop', begin="1999/10/10")
        self.assertEqual(repr(e), "<all-day Event 'plop' 1999-10-10>")

    def test_name_repr(self):
        e = Event(name='plop')
        self.assertEqual(repr(e), "<Event 'plop'>")

    def test_repr(self):
        e = Event(name='plop', begin="1999/10/10 00:00")
        self.assertEqual(repr(e), "<Event 'plop' begin:1999-10-10 00:00:00 end:1999-10-10 00:00:01>")

    def test_init(self):
        e = Event()

        self.assertEqual(e.duration, None)
        self.assertEqual(e.end, None)
        self.assertFalse(e._has_duration())
        self.assertFalse(e._has_end())
        self.assertEqual(e.begin, None)
        self.assertNotEqual(e.uid, None)
        self.assertEqual(e.description, None)
        self.assertNotEqual(e.created, None)
        self.assertEqual(e.location, None)
        self.assertEqual(e.url, None)

    def test_has_end(self):
        e = Event()
        self.assertFalse(e.has_end())
        e = Event(begin="1993/05/24", duration=10)
        self.assertTrue(e.has_end())
        e = Event(begin="1993/05/24", end="1999/10/11")
        self.assertTrue(e.has_end())
        e = Event(begin="1993/05/24")
        e.make_all_day()
        self.assertFalse(e.has_end())

    def test_duration(self):
        e = Event()
        self.assertIsNone(e.duration)

        birthday = Event(begin="1993/05/24")
        self.assertEqual(birthday.duration, timedelta(days=1))

        vacation = Event(begin="1993/05/24", end="1993/05/30")
        self.assertEqual(vacation.duration, timedelta(days=7))

        e3 = Event(begin=datetime(1993, 5, 24, 12),
                   duration=timedelta(minutes=1))
        self.assertEqual(e3.duration, timedelta(minutes=1))

        e4 = Event(begin=datetime(1993, 5, 24, 12))
        self.assertEqual(e4.duration, timedelta(seconds=1))

        e5 = Event(begin=datetime(1993, 5, 24, 12))
        e5.duration = {'days': 6, 'hours': 2}
        self.assertEqual(e5.end, parse_date_or_datetime("1993/05/30T14:00"))
        self.assertEqual(e5.duration, timedelta(hours=146))

    def test_always_uid(self):
        e = Event()
        uid = e.uid  # uid is generated when accessed
        self.assertIn('UID:', str(e))
        self.assertIn(uid, str(e))

    def test_cmp_other(self):
        with self.assertRaises(NotImplementedError):
            Event() < 1
        with self.assertRaises(NotImplementedError):
            Event() > 1
        with self.assertRaises(NotImplementedError):
            Event() <= 1
        with self.assertRaises(NotImplementedError):
            Event() >= 1

    def test_cmp_by_name(self):
        self.assertGreater(Event(name="z"), Event(name="a"))
        self.assertGreaterEqual(Event(name="z"), Event(name="a"))
        self.assertGreaterEqual(Event(name="m"), Event(name="m"))

        self.assertLess(Event(name="a"), Event(name="z"))
        self.assertLessEqual(Event(name="a"), Event(name="z"))
        self.assertLessEqual(Event(name="m"), Event(name="m"))

    def test_cmp_by_name_fail(self):
        self.assertFalse(Event(name="a") > Event(name="z"))
        self.assertFalse(Event(name="a") >= Event(name="z"))

        self.assertFalse(Event(name="z") < Event(name="a"))
        self.assertFalse(Event(name="z") <= Event(name="a"))

    def test_cmp_by_name_fail_not_equal(self):
        self.assertFalse(Event(name="a") > Event(name="a"))
        self.assertFalse(Event(name="b") < Event(name="b"))

    def test_unescape_summarry(self):
        c = Calendar(cal15)
        e = c.events[0]
        self.assertEqual(e.name, "Hello, \n World; This is a backslash : \\ and another new \n line")

    def test_unescapte_texts(self):
        c = Calendar(cal15)
        e = c.events[1]
        self.assertEqual(e.name, "Some special ; chars")
        self.assertEqual(e.location, "In, every text field")
        self.assertEqual(e.description, "Yes, all of them;")

    def test_escape_output(self):
        e = Event()

        e.name = "Hello, with \\ spechial; chars and \n newlines"
        e.location = "Here; too"
        e.description = "Every\nwhere ! Yes, yes !"
        e.created = datetime(2013, 1, 1, tzinfo=tzutc)
        e.uid = "empty-uid"

        output = str(e).splitlines()
        self.assertEqual(output[0], "BEGIN:VEVENT")
        self.assertEqual(output[-1], "END:VEVENT")
        eq = set(("DTSTAMP:20130101T000000Z",
                  "SUMMARY:Hello\\, with \\\\ spechial\\; chars and \\n newlines",
                  "DESCRIPTION:Every\\nwhere ! Yes\\, yes !",
                  "LOCATION:Here\\; too",
                  "UID:empty-uid"))
        self.assertEqual(set(output[1:-1]), eq)

    def test_url_input(self):
        c = Calendar(cal16)
        e = c.events[0]
        self.assertEqual(e.url, "http://example.com/pub/calendars/jsmith/mytime.ics")

    def test_url_output(self):
        URL = "http://example.com/pub/calendars/jsmith/mytime.ics"
        e = Event(name="Name", url=URL)
        self.assertIn("URL:"+URL, str(e).splitlines())
