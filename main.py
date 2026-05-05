import cv2
from security_system import IntelligentSecuritySystem

def main():
    # Initialize the security system
    system = IntelligentSecuritySystem()
    
    # Open camera (0 for default camera)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Security system active. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process the frame
        result = system.process_frame(frame)
        
        # Display results
        if 'annotated_frame' in result:
            cv2.imshow('Security System', result['annotated_frame'])
        
        # Display analysis in console
        if result['faces_detected'] > 0:
            system.display_result(result)
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    system.cleanup()

if __name__ == "__main__":
    main()