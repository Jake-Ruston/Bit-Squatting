from argparse import ArgumentParser
import requests
import time

# TODO
# Case sensitive domains don't need to be added
# Weird case when using jake-ruston.com as an example, the domain "ruston" is returned

class BitSquat:
	def __init__(self):
		self.args = self.parse_arguments()
	
	def parse_arguments(self):
		parser = ArgumentParser(description="Generate a list of domain names with each bit flipped respectively.")

		required = parser.add_argument_group("required arguments")
		required.add_argument("--api-key", help="a GoDaddy production API key", required=True)
		required.add_argument("--domain", help="the domain to bitsquat", required=True)

		parser.add_argument("--available", help="only show available domains", action="store_true")

		return parser.parse_args()

	def check_availability(self, domain):
		headers = {"Authorization":f"sso-key {self.args.api_key}"}
		params = {"domain":domain}
		
		request = requests.get("https://api.godaddy.com/v1/domains/available", headers=headers, params=params)

		if request.status_code != 200:
			error = request.json()["code"]

			if error == "MALFORMED_CREDENTIALS" or error == "UNABLE_TO_AUTHENTICATE":
				print(f"Error: Invalid credentials - {domain}")
				quit()

			if error == "INVALID_BODY":
				print(f"Error: Invalid domain - {domain}")
				quit()

			if error == "UNSUPPORTED_TLD":
				print(f"Error: Invalid TLD - {domain}")
				quit()

			if error == "TOO_MANY_REQUESTS":
				print(f"Error: Ratelimited")
				quit()

		return request

	def get_domains(self, domain):
		domains_binary = []

		hostname, tld = domain.split(".", 1)
		
		domain_binary = "".join(format(ord(char), "08b") for char in hostname)
		domains_binary.append(domain_binary)

		current = 0
		
		while current != len(domain_binary):
			bit = "0" if domain_binary[current] == "1" else "1"

			new_domain_binary = domain_binary[:current] + bit + domain_binary[current + 1:]
			domains_binary.append(new_domain_binary)

			current += 1

		for new_domain_binary in domains_binary:
			domain_str = ""
			
			for char in range(0, len(new_domain_binary), 8):
				temp_data = new_domain_binary[char:char + 8]
				decimal_data = int(temp_data, 2)

				if chr(decimal_data) == ".":
					continue

				domain_str += chr(decimal_data)

			request = self.check_availability(domain_str + f".{tld}")

			if request.status_code == 200:
				if request.json()["available"]:
					print(f"{'' if self.args.available else '[+] '}{domain_str}.{tld}")
				else:
					if not self.args.available:
						print(f"[-] {domain_str}.{tld}")
			else:
				if not self.args.available:
					print(f"[!] {domain_str}.{tld} - {request.json()['code']}")

			time.sleep(1)
	
	def run(self):
		self.get_domains(self.args.domain)

try:
	BitSquat().run()
except KeyboardInterrupt:
	quit()
