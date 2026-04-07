The purpose of this project is to automate the entire workflow of
creating and publishing YouTube Shorts across multiple
channels. It begins by using the YouTube Data API to search and
fetch videos based on specific search criteria provided by the
user. To extract meaningful and engaging content from these
videos, prompt engineering is applied to identify the most
relevant clips with caption. These clips are then trimmed and
processed using the FFmpeg library to fit the short-form video
format. For enhanced visual appeal, the trimmed clips are
combined with footage-such as gameplay or aesthetic loops. To
ensure accessibility and boost viewer engagement, OpenAI's
Whisper API is used to generate accurate subtitles, which are
then burned directly onto the video using FFmpeg. Finally, the
processed video is automatically uploaded or scheduled for
posting on one or more YouTube channels. This fully automated
pipeline eliminates the manual effort typically involved in content
creation.
V2---
Building a policy-learning autonomous editor that learns to
compose editing operations (cut, trim, music sync, transitions,
subtitles, zoom) through hierarchical decision-making instead of
hardcoded rule pipelines.
Implemented a policy-guided search strategy (beam-style
trajectory expansion) to optimize long-horizon editing sequences
under coherence and pacing constraints. Designed a
SegmentState representation from multimodal signals.
Implemented action masking and reward shaping for editing
coherence.Using FFmpeg as deterministic execution
backend. Exploring weak supervision from engagement signals.
Targeting research publication ICMR/ACM multimedia
