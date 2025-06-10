from dotenv import load_dotenv
import os
load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from openai import OpenAI

# Load environment variables
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)
app = App(token=SLACK_BOT_TOKEN)

# --- CAPTION GENERATOR ---
def generate_caption(topic, post_type):
    if post_type == "news":
        prompt = (
            "You're a social media caption writer for a hip-hop brand. "
            "Generate a news-style caption with a call to action like 'drop it below ⬇️'. Don't use any hashtags. The caption must be accurate when relating it to current news. For example, if the topic mentions Kendrick lamar finishing his tour, it should repeat that Kendrick lamar just finished his tour if in reality his tour just started"
            "\n\nExample Topics & Captions:\n"
            "Topic: Drake announces summer European tour with partynextdoor\n"
            "Caption:Drake is officially returning to Europe for the first time in 6 YEARS 🇬🇧🔥 He’s teaming up with PARTYNEXTDOOR for a summer takeover 🦉 Is Drake coming to your city⁉️ Let us know down below ⬇️\n"
            "Topic: Travis's 'Jackboys 2' could potentially be dropping next week\n"
            "Caption: Travis Scott’s ‘JACKBOYS 2’ merch website is saying all items will be “shipped by 6/20” which is next Friday 👀 Are you ready for new music from Travis⁉️ Drop your thoughts below ⬇️\n"
            "Topic: Clout festival announce their 2025 lineup\n"
            "Caption: Clout festival just dropped their 2025 lineup featuring headliners Young Thug, A$AP Rocky, Ken Carson, Yeat, Ferg, Denzel Curry and more ‼️🎤🌟 Which artist are you the most excited to see live⁉️ Let us know in the comments ⬇️\n"
        )
    elif post_type == "birthday":
        prompt = (
            "You're a social media writer for a hip-hop brand. "
            "Write a Happy Birthday post caption that's celebratory, optionally includes the artist's age or legacy, and ends with a fun call to action like '🎂 Drop your favorite track below ⬇️'"
            "\n\nExample:\n"
            "Topic: Happy Birthday Ye\n"
            "Caption: Happy Birthday to Ye 🎂 He turns 48 today. From soul-sampling beats to genre-bending albums. What’s your favorite Ye song or album⁉️ Let us know in the comments ⬇️\n"
            "Topic: Happy Birthday Central Cee\n"
            "Caption: Happy birthday to Central Cee 🎉 He turns 27 today. Over the last few years, Cench has become one of the biggest names in UK rap — breaking records, borders, and expectations with every release. His distinct flow, global mindset, and relentless work ethic have made him a true standout in the drill scene and beyond. What’s your favorite Central Cee song⁉️ Drop it in the comments ⬇️\n"   
            "Topic: Happy Birthday Lucki\n"
            "Caption: Happy birthday to Lucki 🎂 He turns 29 today. For over a decade Lucki has been one of the most consistent, influential, and underrated voices in rap. Over the last few years he has started to gain the mainstream recognition he has so long deserved. The last slide features Tune in 2016 performing in SoHo, just after changing his name from “Lucki Eck$”. Lucki had dropped his 2016 tape ‘Son Of Sam’ just a few months before this performance. This was his first official project under the name Lucki. What’s your favorite Lucki project⁉️ Let us know yours down below ⬇️\n"
        )
    elif post_type == "quote":
        prompt = (
            "You're a social media caption writer for a hip-hop brand. "
            "Create an engaging caption to go along with a quote from an artist. "
            "The caption should give context and ask the audience what they think. The caption should also use relevant information from the internet to provide more context about the quote. End with a CTA like 'Agree or nah? ⬇️'"
            "\n\nExample:\n"
            "Topic: 'Tyler the creator thanks his fans as he wraps up the Europe leg of the Chromokopia tour\n"
            "Caption:'Tyler, The Creator just wrapped up the Europe leg of his CHROMAKOPIA tour and had nothing but love for the fans overseas. He posted “thank you to everyone who came to a show. europe run was amazing. thank you” What was your favorite moment from this tour so far⁉️ Drop it in the comments ⬇⬇️\n"
            "Topic: 'Don Toliver shares a message to his london fans'\n"
            "Caption:'Don Toliver had a message for his London fans after a legendary show at the O2 Arena 🇬🇧🔥 “Words just can’t describe certain things. This was one of uhm...” What was your favorite moment from his tour so far⁉️ Drop it in the comments ⬇️\n"
        )
    else:
        prompt = "Write a hip-hop caption for this topic."

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Topic: {topic}"}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.9,
        max_tokens=150
    )
    return response.choices[0].message.content

# --- INITIAL MESSAGE HANDLER ---
@app.message("")
def handle_initial_message(message, say):
    topic = message.get('text', '').strip()
    say(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔥 *Choose the post format:*"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📰 Standard News"},
                        "action_id": "generate_news",
                        "value": topic
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🎉 Birthday Post"},
                        "action_id": "generate_birthday",
                        "value": topic
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "💬 Quote Post"},
                        "action_id": "generate_quote",
                        "value": topic
                    }
                ]
            }
        ],
        text="Choose post type"
    )

# --- GENERATE ACTION HANDLER ---
def handle_caption_action(ack, body, client, post_type):
    ack()
    topic = body["actions"][0]["value"]

    # Step 1: Send placeholder "Generating..." message
    loading_response = client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"⏳ *Generating caption...*"}
            }
        ],
        text="Generating caption..."
    )

    # Step 2: Generate caption from OpenAI
    result = generate_caption(topic, post_type)

    # Step 3: Replace with actual result and regenerate button
    client.chat_update(
        channel=body["channel"]["id"],
        ts=body["message"]["ts"],
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"* Caption ({post_type.capitalize()}):* \n\n{result}"}
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔁 Regenerate"},
                        "action_id": f"regenerate_{post_type}",
                        "value": topic
                    }
                ]
            }
        ],
        text=result
    )

# Bind post-type buttons to the generator
@app.action("generate_news")
def generate_news(ack, body, client): handle_caption_action(ack, body, client, "news")

@app.action("generate_birthday")
def generate_birthday(ack, body, client): handle_caption_action(ack, body, client, "birthday")

@app.action("generate_quote")
def generate_quote(ack, body, client): handle_caption_action(ack, body, client, "quote")

# Bind regenerate actions
@app.action("regenerate_news")
def regenerate_news(ack, body, client): handle_caption_action(ack, body, client, "news")

@app.action("regenerate_birthday")
def regenerate_birthday(ack, body, client): handle_caption_action(ack, body, client, "birthday")

@app.action("regenerate_quote")
def regenerate_quote(ack, body, client): handle_caption_action(ack, body, client, "quote")

# --- RUN APP ---
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
