
import requests
try:
    print('Sending POST request...')
    response = requests.post('http://127.0.0.1:5000/process', data={'url': 'https://www.ana-white.com/woodworking-projects/cup-tree'})
    print('Status Code:', response.status_code)
    if response.status_code == 200:
        with open('Premium_Plan_Test.pdf', 'wb') as f:
            f.write(response.content)
        print('Saved Premium_Plan_Test.pdf')
    else:
        print('Response:', response.text)
except Exception as e:
    print('Error:', e)

