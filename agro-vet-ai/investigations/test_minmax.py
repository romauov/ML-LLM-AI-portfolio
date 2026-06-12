from openai import OpenAI

client = OpenAI(
  base_url="https://api.minimax.io/v1", 
  api_key="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJBbGV4YW5kciBHb3Jsb3YiLCJVc2VyTmFtZSI6IkFsZXhhbmRyIEdvcmxvdiIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTg2NzE3NTIzNzY0MDYwMTk0IiwiUGhvbmUiOiIiLCJHcm91cElEIjoiMTk4NjcxNzUyMzc1OTg2MTc5NCIsIlBhZ2VOYW1lIjoiIiwiTWFpbCI6ImEuZ29ybG92QGdtYWlsLmNvbSIsIkNyZWF0ZVRpbWUiOiIyMDI1LTExLTA3IDE3OjAxOjE4IiwiVG9rZW5UeXBlIjoxLCJpc3MiOiJtaW5pbWF4In0.K086oMSCmX4s5eBM_pYgeF21HPQiT8P1Tnj2AjiFSH2DGir4JbeI0wU8KJlnyMHDqAstd2O9gD83_DAUEPt2TRQxw2iJRTnx4dcy49iIUuBd7FmaYGAYWMvpJqWC560rS77pIJfCqaQN3dolf40d8oyyHNbPl5Le1c4N9cmbd7BteTcDj7QnAtRnTiLx79cZvdV7BOteezFLfBIaO12rAmjQSw0zt_joDMYy1jlnyBCmx6wUnNwfvLwuB0DmKzFBpX2RJDDmQM_y9NmsCro0duYMpG2OZa5Hlt0w_3qGWgssY9Z4KDt35x_QIW8bk6jZwF2i6z7e_48esFu2GW_HGg"
)

response = client.chat.completions.create(
    model="MiniMax-M2",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hi, how are you?"},
    ],
    # Set reasoning_split=True to separate thinking content into reasoning_details field
    extra_body={"reasoning_split": True},
)

print(f"Thinking:\n{response.choices[0].message.reasoning_details[0]['text']}\n")
print(f"Text:\n{response.choices[0].message.content}\n")