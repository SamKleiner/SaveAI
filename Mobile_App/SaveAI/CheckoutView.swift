//
//  CheckoutView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI

struct CheckoutView: View {
    @ObservedObject var saleViewModel: SaleViewModel
    
    var body: some View {
        VStack {
            if let sale = saleViewModel.currentSale {
                Text("Total: \(sale.formattedTotal)")
                    .font(.largeTitle)
                    .padding()
                Button("Complete Sale") {
                    saleViewModel.completeSale()
                }
                .padding()
            } else {
                Text("No sale in progress")
            }
        }
        .padding()
    }
}
