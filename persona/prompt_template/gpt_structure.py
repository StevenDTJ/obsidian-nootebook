"""
Author: Joon Sung Park (joonspk@stanford.edu)

File: gpt_structure.py
Description: Wrapper functions for calling DeepSeek APIs.
Modified to use DeepSeek Chat model instead of OpenAI.
"""
import json
import random
import requests  # 使用 requests 调用 DeepSeek API
import time

from utils import *

# DeepSeek API 配置
DEEPSEEK_API_KEY = openai_api_key  # 使用 utils.py 中的 API Key
DEEPSEEK_API_BASE = "https://api.deepseek.com"  # DeepSeek API 基础 URL

# Qwen API 配置 (从 utils.py 读取)
try:
    QWEN_EMBEDDING_API_KEY = qwen_api_key  # 从 utils.py 获取 Qwen API Key
    get_embedding.qwen_api_key = QWEN_EMBEDDING_API_KEY
except:
    QWEN_EMBEDDING_API_KEY = None
    get_embedding.qwen_api_key = None

def temp_sleep(seconds=0.1):
  time.sleep(seconds)

def DeepSeek_chat_request(prompt, model="deepseek-chat"):
  """
  调用 DeepSeek Chat API
  """
  temp_sleep()

  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
  }

  payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.7,
    "max_tokens": 2048
  }

  try:
    response = requests.post(
      f"{DEEPSEEK_API_BASE}/v1/chat/completions",
      headers=headers,
      json=payload,
      timeout=120
    )
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]
  except Exception as e:
    print(f"DeepSeek API Error: {e}")
    return "DeepSeek ERROR"

def DeepSeek_chat_request_with_params(prompt, model="deepseek-chat", temperature=0.7, max_tokens=2048):
  """
  带参数的 DeepSeek Chat API 调用
  """
  temp_sleep()

  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
  }

  payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "temperature": temperature,
    "max_tokens": max_tokens
  }

  try:
    response = requests.post(
      f"{DEEPSEEK_API_BASE}/v1/chat/completions",
      headers=headers,
      json=payload,
      timeout=120
    )
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]
  except Exception as e:
    print(f"DeepSeek API Error: {e}")
    return "DeepSeek ERROR"


# ============================================================================
# #####################[SECTION 1: DEEPSEEK CHAT STRUCTURE] ###################
# ============================================================================

# 兼容旧接口 - 映射到 DeepSeek
def ChatGPT_single_request(prompt):
  """兼容旧接口，使用 DeepSeek"""
  return DeepSeek_chat_request(prompt, model="deepseek-chat")


def GPT4_request(prompt):
  """
  使用 DeepSeek Chat 替代 GPT-4
  """
  return DeepSeek_chat_request(prompt, model="deepseek-chat")


def ChatGPT_request(prompt):
  """
  使用 DeepSeek Chat 替代 GPT-3.5
  """
  return DeepSeek_chat_request(prompt, model="deepseek-chat")


def GPT4_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = GPT4_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response(prompt, 
                                   example_output,
                                   special_instruction,
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  # prompt = 'GPT-3 Prompt:\n"""\n' + prompt + '\n"""\n'
  prompt = '"""\n' + prompt + '\n"""\n'
  prompt += f"Output the response to the prompt above in json. {special_instruction}\n"
  prompt += "Example output json:\n"
  prompt += '{"output": "' + str(example_output) + '"}'

  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 

    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      end_index = curr_gpt_response.rfind('}') + 1
      curr_gpt_response = curr_gpt_response[:end_index]
      curr_gpt_response = json.loads(curr_gpt_response)["output"]

      # print ("---ashdfaf")
      # print (curr_gpt_response)
      # print ("000asdfhia")
      
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      
      if verbose: 
        print ("---- repeat count: \n", i, curr_gpt_response)
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass

  return False


def ChatGPT_safe_generate_response_OLD(prompt, 
                                   repeat=3,
                                   fail_safe_response="error",
                                   func_validate=None,
                                   func_clean_up=None,
                                   verbose=False): 
  if verbose: 
    print ("CHAT GPT PROMPT")
    print (prompt)

  for i in range(repeat): 
    try: 
      curr_gpt_response = ChatGPT_request(prompt).strip()
      if func_validate(curr_gpt_response, prompt=prompt): 
        return func_clean_up(curr_gpt_response, prompt=prompt)
      if verbose: 
        print (f"---- repeat count: {i}")
        print (curr_gpt_response)
        print ("~~~~")

    except: 
      pass
  print ("FAIL SAFE TRIGGERED") 
  return fail_safe_response


# ============================================================================
# ###################[SECTION 2: ORIGINAL DEEPSEEK STRUCTURE] ###################
# ============================================================================

def GPT_request(prompt, gpt_parameter):
  """
  Given a prompt and a dictionary of GPT parameters, make a request to DeepSeek
  server and returns the response.
  ARGS:
    prompt: a str prompt
    gpt_parameter: a python dictionary with the keys indicating the names of
                   the parameter and the values indicating the parameter
                   values.
  RETURNS:
    a str of DeepSeek's response.
  """
  temp_sleep()

  # 从 gpt_parameter 中提取参数
  model = gpt_parameter.get("engine", "deepseek-chat")
  temperature = gpt_parameter.get("temperature", 0.7)
  max_tokens = gpt_parameter.get("max_tokens", 2048)

  try:
    return DeepSeek_chat_request_with_params(prompt, model=model, temperature=temperature, max_tokens=max_tokens)
  except:
    print("DEEPSEEK ERROR")
    return "DEEPSEEK ERROR"


def generate_prompt(curr_input, prompt_lib_file):
  """
  Takes in the current input (e.g. comment that you want to classifiy) and
  the path to a prompt file. The prompt file contains the raw str prompt that
  will be used, which contains the following substr: !<INPUT>! -- this
  function replaces this substr with the actual curr_input to produce the
  final promopt that will be sent to the DeepSeek server.
  ARGS:
    curr_input: the input we want to feed in (IF THERE ARE MORE THAN ONE
                INPUT, THIS CAN BE A LIST.)
    prompt_lib_file: the path to the promopt file.
  RETURNS:
    a str prompt that will be sent to DeepSeek's server.
  """
  if type(curr_input) == type("string"): 
    curr_input = [curr_input]
  curr_input = [str(i) for i in curr_input]

  f = open(prompt_lib_file, "r")
  prompt = f.read()
  f.close()
  for count, i in enumerate(curr_input):   
    prompt = prompt.replace(f"!<INPUT {count}>!", i)
  if "<commentblockmarker>###</commentblockmarker>" in prompt: 
    prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[1]
  return prompt.strip()


def safe_generate_response(prompt, 
                           gpt_parameter,
                           repeat=5,
                           fail_safe_response="error",
                           func_validate=None,
                           func_clean_up=None,
                           verbose=False): 
  if verbose: 
    print (prompt)

  for i in range(repeat): 
    curr_gpt_response = GPT_request(prompt, gpt_parameter)
    if func_validate(curr_gpt_response, prompt=prompt): 
      return func_clean_up(curr_gpt_response, prompt=prompt)
    if verbose: 
      print ("---- repeat count: ", i, curr_gpt_response)
      print (curr_gpt_response)
      print ("~~~~")
  return fail_safe_response


# Qwen Embedding API 配置
QWEN_API_BASE = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding"

def get_embedding(text, model="text-embedding-v1"):
  """
  获取文本嵌入向量
  优先使用 Qwen Embedding (阿里云)，失败时回退到 OpenAI
  """
  text = text.replace("\n", " ")
  if not text:
    text = "this is blank"

  # 优先尝试使用 Qwen Embedding (阿里云)
  try:
    if hasattr(get_embedding, 'qwen_api_key') and get_embedding.qwen_api_key:
      headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_embedding.qwen_api_key}"
      }
      payload = {
        "model": "text-embedding-v1",
        "input": text
      }
      response = requests.post(
        QWEN_API_BASE,
        headers=headers,
        json=payload,
        timeout=60
      )
      response.raise_for_status()
      result = response.json()
      return result["output"]["embeddings"][0]["embedding"]
  except Exception as e:
    print(f"Qwen Embedding API Error: {e}")

  # 回退到 OpenAI embedding
  try:
    import openai
    openai.api_key = DEEPSEEK_API_KEY
    return openai.Embedding.create(
      input=[text],
      model="text-embedding-3-small"
    )['data'][0]['embedding']
  except Exception as e:
    print(f"OpenAI Embedding API Error: {e}")
    # 最后回退到 text-embedding-ada-002
    try:
      import openai
      openai.api_key = DEEPSEEK_API_KEY
      return openai.Embedding.create(
        input=[text],
        model="text-embedding-ada-002"
      )['data'][0]['embedding']
    except:
      return None

# 用于存储 Qwen API Key
get_embedding.qwen_api_key = None

def set_qwen_api_key(api_key):
  """设置 Qwen API Key"""
  get_embedding.qwen_api_key = api_key


if __name__ == '__main__':
  gpt_parameter = {"engine": "deepseek-chat", "max_tokens": 50,
                   "temperature": 0, "top_p": 1, "stream": False,
                   "frequency_penalty": 0, "presence_penalty": 0,
                   "stop": ['"']}
  curr_input = ["driving to a friend's house"]
  prompt_lib_file = "prompt_template/test_prompt_July5.txt"
  prompt = generate_prompt(curr_input, prompt_lib_file)

  def __func_validate(gpt_response):
    if len(gpt_response.strip()) <= 1:
      return False
    if len(gpt_response.strip().split(" ")) > 1:
      return False
    return True
  def __func_clean_up(gpt_response):
    cleaned_response = gpt_response.strip()
    return cleaned_response

  output = safe_generate_response(prompt,
                                 gpt_parameter,
                                 5,
                                 "rest",
                                 __func_validate,
                                 __func_clean_up,
                                 True)

  print (output)




















