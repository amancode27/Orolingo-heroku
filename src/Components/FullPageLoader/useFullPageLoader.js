import React, { useState } from 'react';
import FullPageLoader from './FullPageLoader';

const useFullPageLoader = () => {
    const [loading, setLoading] = useState(false)

    return [
        loading ? <FullPageLoader /> : null,
        () => setLoading(true), 
        () => setLoading(false)
    ]
}

export default useFullPageLoader;
