import SwiftUI

struct Sound: Codable {
    let classification: String
    let content: String
    let speaking: String
}

struct ContentView: View {
    @State private var sound1 = "";
    @State private var sound2 = "";
    @State private var sound3 = "";
    @State private var sound4 = "";
    
    let timer = Timer.publish(every: 0.5, on: .current, in: .common).autoconnect()

    var body: some View {
        VStack (spacing: 9) {
            Text(sound1).padding(EdgeInsets(top: 3, leading: 10, bottom: 3, trailing: 10)).background(Color.white.opacity(0.4)).cornerRadius(15).font(.system(size: 20))
            Text(sound2).padding(EdgeInsets(top: 3, leading: 10, bottom: 3, trailing: 10)).background(Color.white.opacity(0.4)).cornerRadius(15).font(.system(size: 20))
            Text(sound3).padding(EdgeInsets(top: 3, leading: 10, bottom: 3, trailing: 10)).background(Color.white.opacity(0.4)).cornerRadius(15).font(.system(size: 20))
            Text(sound4).padding(EdgeInsets(top: 3, leading: 10, bottom: 3, trailing: 10)).background(Color.white.opacity(0.4)).cornerRadius(15).font(.system(size: 20))
        }.frame(maxWidth: .infinity).onAppear(perform: loadData).onReceive(timer) { _ in
            self.loadData()
        }
    }
}

extension ContentView {
    func loadData() {
        guard let url1 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound1.json") else {
            return
        }
        
        let request1 = URLRequest(url: url1)
        URLSession.shared.dataTask(with: request1) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound1 = decodedData.classification
                    }
                }
            }
        }.resume()
        
        guard let url2 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound2.json") else {
            return
        }
        
        let request2 = URLRequest(url: url2)
        URLSession.shared.dataTask(with: request2) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound2 = decodedData.classification
                    }
                }
            }
        }.resume()
        
        guard let url3 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound3.json") else {
            return
        }
        
        let request3 = URLRequest(url: url3)
        URLSession.shared.dataTask(with: request3) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound3 = decodedData.classification
                    }
                }
            }
        }.resume()
        
        guard let url4 = URL(string: "https://soundy-8d98a-default-rtdb.firebaseio.com/Sound/sound4.json") else {
            return
        }
        
        let request4 = URLRequest(url: url4)
        URLSession.shared.dataTask(with: request4) { data, response, error in
            if let data = data {
                if let decodedData = try? JSONDecoder().decode(Sound.self, from: data) {
                    DispatchQueue.main.async {
                        self.sound4 = decodedData.classification
                    }
                }
            }
        }.resume()
    }
}


struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}

