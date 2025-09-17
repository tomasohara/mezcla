#! /usr/bin/env python3
#
# Downloads transcript for YouTube video
#
# Based on following:
#   https://github.com/jdepoix/youtube-transcript-api/issues/234 [expose functionality for formatting timestamps in textual formats]
#

"""
Download YouTube transcript

Sample usages:
   {script} 'https://www.youtube.com/watch?v=1KcdgFxmnb4' > Caravaggio-examples.txt

   id=3UWxmt7VAlU; {script} "$id" > edward-loper-doc.txt
"""

# Standard modules
## TODO: import json

# Installed modules
import youtube_transcript_api as ytt_api
from youtube_transcript_api import formatters

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import misc_utils
from mezcla.my_regex import my_re
from mezcla import system

# Constants
TL = debug.TL

#-------------------------------------------------------------------------------
# Note: custom class due lack of help by youtube_transcript_api developers

class YouTubeLikeFormatter(formatters._TextBasedFormatter):      # pylint: disable=protected-access
    """Uses format similar to that under YouTube's Transcript pane:
         0:16 This is the city after a storm, ...
         0:23 "Once you learn to see as an artist, ..."""

    def _format_timestamp(self, hours, mins, secs, _ms):
        # format as HH:MM:SS w/ 00 hour omitted and with leading zeros dropped
        timestamp = "{:02d}:{:02d}:{:02d}".format(hours, mins, secs)
        timestamp = my_re.sub("^00:", "", timestamp)
        timestamp = my_re.sub("^0", "", timestamp)
        return timestamp

    def _format_transcript_header(self, lines):
        return "Transcript\n\n" + "\n".join(lines) + "\n"

    def _format_transcript_helper(self, i, time_text, line):
        # drops second timestamp (e.g., "00:00:28.500 --> 00:00:30.060" => "00:00:28.500")
        time_text = my_re.sub(r" --> \S+", "", time_text)
        return "{} {}".format(time_text, line['text'])

    def format_transcript(self, transcript, **kwargs):
        """Format transcript with YouTube-like timestamps."""
        # Note: fix for attribute problem via Claude-Opus-4
        lines = []
        for i, line in enumerate(transcript):
            timestamp = self._seconds_to_timestamp(line['start'])
            formatted_line = self._format_transcript_helper(i, timestamp, line)
            lines.append(formatted_line)
        return self._format_transcript_header(lines)

#-------------------------------------------------------------------------------

def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Parse command line options, show usage if --help given
    main_app = Main(description=__doc__.format(script=gh.basename(__file__)),
                    skip_input=False, manual_input=False)
    debug.assertion(main_app.parsed_args)
    url = main_app.filename
    video_id= url
    YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="
    if url.startswith(YOUTUBE_PREFIX):
        video_id = url[len(YOUTUBE_PREFIX):]
    else:
        debug.assertion("youtube.com" not in url)
        url = YOUTUBE_PREFIX + url
    ## TODO: video_id = my_re.sub(r"(https://)?www.youtube.com/watch\?v=", "", main_app.filename)
    debug.trace_expr(5, url, video_id)

    # Download the transcript and print using YouTubeLike-format
    # note: youtube_transcript_api
    print(misc_utils.get_formatted_date())
    print("")
    print(url)
    print("")
    try:
        transcript = ytt_api.YouTubeTranscriptApi.get_transcript(video_id)
        debug.trace_expr(5, transcript, max_len=256)
        debug.trace_values(6, transcript, "transcript")
        print(YouTubeLikeFormatter().format_transcript(transcript))
    except:
        system.print_exception_info("transcript access")
        print("n/a")

    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
