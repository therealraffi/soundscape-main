import SwiftUI

struct Country: Decodable {
    var country: String
    var code:String
}



struct ContentView: View {
    @State private var countryData = [Country]()
    
    var body: some View {
        List(countryData, id: \.code) {
            item in
            HStack() {
                Text(item.country)
                Text(item.code)
            }
        }.onAppear(perform: loadData)
    }
}

extension ContentView {
    func loadData() {
        
        guard let url = URL(string: "https://kaleidosblog.s3-eu-west-1.amazonaws.com/json/tutorial.json") else {
            return
        }
        
        let request = URLRequest(url: url)
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let data = data {
                if let response_obj = try? JSONDecoder().decode([Country].self, from: data) {
                    DispatchQueue.main.async {
                        self.countryData = response_obj
                    }
                }
            }
        }.resume()
        
        let data = Data("""
        {
          "classification" : "babycrying",
          "content" : "babycrying",
          "speaking" : "false"
        }
        """.utf8)

        struct Certification: Codable {
            let classification: String
            let content: String
            let speaking: String
        }

        do {
            let decodedData = try JSONDecoder().decode(Certification.self, from: data)
            print(decodedData)
        } catch { print(error) }
    }
}


struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}

