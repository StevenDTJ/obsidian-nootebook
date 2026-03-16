import whisper

model = whisper.load_model("medium")
result = model.transcribe("附件/Recording 20260316083901.m4a", task="translate")
print(result["text"])
